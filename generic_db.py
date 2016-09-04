import sqlite3
import os

from logging_handler import LoggingHandler
log = LoggingHandler(__name__, max_level='DEBUG')


def split_list(alist,max_size=1):
	"""Yield successive n-sized chunks from l."""
	for i in range(0, len(alist), max_size):
		yield alist[i:i+max_size]

class GenericDatabaseHandler(object):
	"""docstring for GenericDatabaseHandler"""
	def __init__(self, db_filepath):
		super(GenericDatabaseHandler, self).__init__()

		self.db_filepath = db_filepath

	def _createTable(self, table_name, params):
		def get_optional_param(prms, p):
			try:
				res = prms[p]
			except KeyError:
				return None
			return res

		command = "CREATE TABLE {}(".format(table_name)

		col_comms = []
		for col in params:
			col_comm_params = [col['name'], col['type']]
			if get_optional_param(col, 'primary_key'):
				col_comm_params += ['PRIMARY KEY']
			if get_optional_param(col, 'unique'):
				col_comm_params += ['UNIQUE']

			col_comms.append(" ".join(col_comm_params))
			# comm_params += col_comm_params

		command += ",".join(col_comms)
		command += ");"

		try:
			self._run_command(command)
		except sqlite3.OperationalError:
			# table probably already exists
			return False

		return True

	def _getEntryEquals(self, table_name, condition_param, equals_what, *params):
		"""
		Returns the values of parameters from rows where `condition_param` is equal to `equals_what`
		:param condition_param:
		:param equals_what:
		:param params:
		:return: a tuple of tuples. Each subtuple contains one row, all the specified parameters in it.
		"""
		command = "SELECT {0} FROM {1}".format(",".join(params), table_name, condition_param)
		parameters = ()
		if condition_param:
			command += " WHERE {0}==?".format(condition_param)
			parameters = (equals_what,)
		command += ";"

		result = self._run_command(command, parameters)

		return result

	def _addEntry(self, table_name, **params):
		parameters = []
		par_names = []
		for i in params:
			parameters += [params[i]]
			par_names += [i]

		command = "INSERT INTO {0}({1}) VALUES ({2});".format(table_name, ",".join(par_names), ",".join("?"*len(params)))

		try:
			self._run_command(command, parameters)
		except sqlite3.IntegrityError:
			return False

		return True

	def _updateEntriesEqual(self, table_name, condition_param, equals_what, **params):
		"""
		Updates an entry based on equality of a parameter in a row
		:param table_name:
		:param condition_param: parameter to check in the row. If none, no checking is performed, all rows are returned.
		:param equals_what: the parameters from `params` in this row is updated if `condition_param` is equal to this
		:param params: a dictionary of parameters to update in the row.
		:return:
		"""
		command = "UPDATE {0} SET ".format(table_name)

		com_par = []
		parameters = []
		for i in params.keys():
			com_par.append(i + " = ?")
			parameters.append(params[i])
		command += ",".join(com_par)
		command += " WHERE {0}==?;".format(condition_param)
		parameters.append(equals_what)

		self._run_command(command, parameters)

	def _batchAdd(self, table_name, data, *params):
		"""

		:param table_name:
		:param data:
		:param params:
		:return:
		"""
		split_data = split_list(data, 500)

		for d in split_data:
			command = "INSERT INTO {0}({1}) VALUES {2}".format(table_name, ",".join(params), ",".join(
				[
					"({})".format(",".join("?"*len(params)))
				 ]*len(d)
			)
			)
			parameters = sum(d, ())  # flatten
			self._run_command(command, parameters)

	def _batchDeleteEquals(self, table_name, condition_param, in_list):
		"""
		Deletes entries from database if a parameter value is in `in_list`
		:param table_name:
		:param condition_param: this parameter should be in `in_list`, then the entry is deleted
		:param in_list:
		:return:
		"""
		command = "DELETE FROM {0} WHERE {1} in ({2});".format(table_name, condition_param, ",".join(["?",]*len(in_list)))
		parameters = tuple(in_list)

		self._run_command(command, parameters)

	def _run_command(self, command, parameters=()):
		"""
		Runs a given command and returns the output.
		:param command:
		:return:
		"""
		log.debug("Command:", command)
		log.debug("Parameters:", parameters)

		conn = sqlite3.connect(self.db_filepath)
		cursor = conn.execute("PRAGMA synchronous=OFF;")
		cursor = conn.execute(command, parameters)
		data = tuple(i for i in cursor)
		conn.commit()
		conn.close()

		return data

if __name__ == '__main__':
	test_db_filepath = os.path.join("databases", "test_db.db")
	try:
		os.remove(test_db_filepath)
	except FileNotFoundError:
		pass

	h = GenericDatabaseHandler(test_db_filepath)
	h._createTable("test001table", ({'name': "col1", "type": "integer", "unique": True},
									{'name': "col2", "type": "text", "primary_key": True},
									{'name': "col3", "type": "text",},
									))
	h._addEntry("test001table", col1=1, col2="hello", col3="42")
	h._addEntry("test001table", col1=3, col2="Guten Tag", col3="42b")
	h._addEntry("test001table", col1=2, col2="Zdravstvuyte", col3="dunno")
	h._updateEntriesEqual("test001table", 'col1', 1, col2="hola", col3="42b")
	print(h._getEntryEquals("test001table", "col3", "42b", "col2", "col1"))
	print(h._getEntryEquals("test001table", None, "42b", "col2", "col1"))


	# os.remove(test_db_filepath)
