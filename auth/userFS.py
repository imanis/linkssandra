import os


def createFSforUser(username):
	os.mkdir(os.path.join('media/DATA/', username))
	os.mkdir(os.path.join('media/DATA/'+username+'/', 'photo'))
	os.mkdir(os.path.join('media/DATA/'+username+'/', 'cv'))
	

