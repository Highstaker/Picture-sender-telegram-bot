#!/usr/bin/python3 -u
# -*- coding: utf-8 -*-
from os import path, walk

class DictUtils:
	@staticmethod
	def replaceKey(dic, oldkey, newkey):
		try:
			dic[newkey] = dic.pop(oldkey)
		except KeyError:
			raise KeyError("Could not replace key {0}. It was not found!".format(oldkey))

	@staticmethod
	def dictGetCaseInsensitive(dic, key):
		result = None
		try:
			# maybe it already exists as-is
			result = dic[key]
		except KeyError:
			error_message = "The key was not found, even case-insensitively"
			if isinstance(key, str):
				# try to find case-insensitively
				upper_key = key.upper()
				for i in dic:
					if i.upper() == upper_key:
						result = dic[i]
						break
				else:
					raise KeyError(error_message)
			else:
				raise KeyError(error_message)

		return result

class FolderSearch:

	@staticmethod
	def getFilepathsInclSubfolders(FOLDER, allowed_extensions=None):
		"""
		Returns a list of full paths to all files in a folder and subfolders. Follows links!
		param allowed_extensions: if provided, adds only files with specified extensions
		"""
		myFolder = FOLDER
		fileSet = set()

		for root, dirs, files in walk(myFolder,followlinks=True):
			for fileName in files:
				if not allowed_extensions or path.splitext(fileName)[1].replace('.','').lower() in [i.lower() for i in allowed_extensions]:
					fileSet.add( path.join( root, fileName ))
		return list(fileSet)


class DropboxFolderSearch:

	@staticmethod
	def getFilepathsInclSubfoldersDropboxPublic(LINK):
		'''
		Returns a list of full paths to all files in a public folder (provided with a link) and subfolders in Dropbox
		'''

		def readDir(LINK,DIR):
			#Set a loop to retry connection if it is refused
			result = []
			while True:
				try:
					req=requests.post('https://api.dropbox.com/1/metadata/link',data=dict( link=LINK, client_id=DROPBOX_APP_KEY,client_secret=DROPBOX_SECRET_KEY, path=DIR) )

					for i in json.loads(req.content.decode())['contents']:
						if i['is_dir']:
							logging.warning("Reading directory: " + str(i['path']))#debug
							result += readDir(LINK,i['path'])
						else:
							#a file, add to list
							result += [i['path']]

					break
				except:
					sleep(60)#wait a bit before retrying
					pass

			return result

		filelist = readDir(LINK,"/")

		return filelist
