from threading import Thread
from os import path
import requests
import json

from textual_data import METADATA_FILENAME
from utils import DropboxFolderSearch
from logging_handler import LoggingHandler
log = LoggingHandler(__name__, max_level="DEBUG")

IMAGE_FILE_EXTENSIONS = (".jpg", ".jpeg", ".png",)
AUX_FILES = (METADATA_FILENAME,)  # various filenames, like metadata, collections info, etc.


def is_pic(filepath):
	return path.splitext(filepath)[1].lower() in IMAGE_FILE_EXTENSIONS


def is_auxfile(filepath):
	return path.basename(filepath) in AUX_FILES


def is_metadata(filepath):
	return path.basename(filepath) == METADATA_FILENAME


class DropboxHandler(object):
	"""docstring for DropboxManager"""
	def __init__(self, database_handler):
		super(DropboxHandler, self).__init__()

		with open(path.join("links", "DB_public_link"), 'r') as f:
			self.DB_link = f.readline()

		log.debug("DB_link", self.DB_link)

		with open(path.join("tokens", "dropbox_tokens"), 'r') as f:
			self.DB_appkey = f.readline().split('#')[0].strip(" \n\t\r")
			self.DB_secretkey = f.readline().split('#')[0].strip(" \n\t\r")

		log.debug("DB_appkey", self.DB_appkey)
		log.debug("DB_secretkey", self.DB_secretkey)

		self.database_handler=database_handler

	def updateFiles(self):
		t = Thread(target=self._updaterThread)
		t.start()

	def _updaterThread(self):
		def filtr(l):
			for f in l:
				filename = f[0]
				if is_pic(filename) or is_auxfile:
					yield f

		def dictionarize(l):
			result = {}
			for f in l:
				filepath = f[0]
				sub_dict = {}
				try:
					sub_dict['mod_time'] = f[1]
					sub_dict['file_type'] = f[2]
				except IndexError:
					pass
				result[filepath] = sub_dict

			return result



		db_files_and_mods = DropboxFolderSearch.getFilepathsInclSubfoldersDropboxPublic(self.DB_link,
																	self.DB_appkey,
																	self.DB_secretkey,
																	)
		db_files_and_mods = dictionarize(filtr(db_files_and_mods))
		# log.debug("db_files_and_mods", db_files_and_mods)

		bd_files_and_mods = dictionarize(self.database_handler.getFilesModtimesTypes())
		# log.debug("bd_files_and_mods", bd_files_and_mods)

		db_files = set(db_files_and_mods.keys())
		bd_files = set(bd_files_and_mods.keys())
		# log.debug("db_files", db_files)
		# log.debug("bd_files", bd_files)

		# deleting nonexistent files from database
		to_delete = bd_files.difference(db_files)
		self.database_handler.batchDeleteFiles(to_delete)
		del to_delete

		# adding files
		to_add = db_files.difference(bd_files)
		# get pictures and add to database
		pics_to_add = set(i for i in to_add if is_pic(i))
		data_to_add = tuple((i, db_files_and_mods[i]['mod_time'], 1,) for i in db_files if i in pics_to_add)
		self.database_handler.batchAddFiles(data_to_add, type="pic")
		del pics_to_add
		# get metas
		metas_to_add = set(i for i in to_add if is_metadata(i))
		# get the contents of metafiles
		data_to_add = tuple((i, db_files_and_mods[i]['mod_time'], self.getDropboxFile(i).decode("utf-8"), 2)
							for i in db_files if i in metas_to_add)
		self.database_handler.batchAddFiles(data_to_add, type="meta")
		del metas_to_add
		del data_to_add
		del to_add

		# scan for modified files
		to_be_scanned = db_files.intersection(bd_files)
		pass
		for filepath in to_be_scanned:
			bd_mod_time = bd_files_and_mods[filepath]['mod_time']
			file_type = bd_files_and_mods[filepath]['file_type']
			if bd_mod_time:
				db_mod_time = db_files_and_mods[filepath]['mod_time']
				# if "Empty" in filepath: print(filepath, bd_mod_time, db_mod_time)#debug
				if bd_mod_time < db_mod_time:
					if file_type == 1:  # picture
						self.database_handler.invalidateCache(filepath)
					elif file_type == 2:  # metafile
						content = self.getDropboxFile(filepath).decode("utf-8")
						self.database_handler.updateMetafileContent(filepath, content)
					self.database_handler.updateModtime(filepath, db_mod_time)



	def getDropboxFile(self, filepath):
		"""
		Gets the data from a file in Dropbox
		:param filepath: path to a file in Dropbox
		:return:  bytestring containing data from file
		"""
		data = None
		# First, get metadata of a file. It contains a direct link to it!
		req = requests.post('https://api.dropbox.com/1/metadata/link',
							data=dict(link=self.DB_link,
									  client_id=self.DB_appkey,
									  client_secret=self.DB_secretkey,
									  path=filepath), timeout=5)
		if req.ok:
			# If metadata got grabbed, extract a link to a file and make a downloadable version of it
			req = json.loads(req.content.decode())['link'].split("?")[0] + "?dl=1"
			# Now let's get the file contents
			try:
				req = requests.get(req, timeout=5)
				if req.ok:
					data = req.content
			except:
				data = None
		else:
			# handle absence of file (maybe got deleted?)
			data = None

		return data


if __name__ == '__main__':
	from database_handler import DatabaseHandler
	dh = DropboxHandler(DatabaseHandler())
	dh.updateFiles()
