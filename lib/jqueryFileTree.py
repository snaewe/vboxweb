"""
	$Id$
	Copyright (C) 2010 Ian Moore (imoore76 at yahoo dot com)
"""

import os
import re

class jqueryFileTree:

	dirsOnly = False
	strDSEP = '/'
	allowedFiles = {}
	allowedFolders = {}
	dir = '/'
	mode = 'local'
	fullpath = False
	vbox = None
	
	# Generic starter function
	def getdir(self,dir):
		
		# In some cases, "dir" passed is just a file name
		if not (dir and str(dir).find(self.strDSEP) != -1):
			dir = self.strDSEP
				
		# String to be returned to browser
		RETURNSTR = ''
		
	    # Check that folder restriction validates if it exists 
		if dir != '/' and len(self.allowedFolders):
			valid = False
			for f in self.allowedFolders:
				if dir.lower().find(f) == 0:
					valid = True
					break
			
			if not valid:
				RETURNSTR += self.folder_start()
				RETURNSTR += '<li>Access denied to '+dir+'</li>'
				RETURNSTR += self.folder_end()
				dir = '/'
	    	
		# Folder Restriction with root '/' requested
		if dir == '/' and len(self.allowedFolders):
			RETURNSTR += self.folder_start()
			for f in self.allowedFolders:
				RETURNSTR += self.folder_folder(f,True)
	    		
			RETURNSTR += self.folder_end()
			return RETURNSTR

		# Full, expanded path to dir ?
		if self.fullpath:
			RETURNSTR += self.folder_start()
			if len(self.allowedFolders):
				RETURNSTR += folder_start()
				for f in self.allowedFolders:
					if (dir.lower() != f) and dir.lower().find(f) == 0:
						RETURNSTR += folder_folder(f,True,True)
						path = dir[len(f)+1:]
						path = re.split('[/|\\\]',path)
						RETURNSTR += self.printdir(f,path)
					else:
						RETURNSTR += self.folder_folder(f,True)
				RETURNSTR += self.folder_end()
			else:
				dir = re.split('[/|\\\]',dir)
				root = dir.pop(0)+self.strDSEP
				RETURNSTR += self.folder_folder(root,True,True)
				RETURNSTR += self.printdir(root,dir)
				RETURNSTR += '</li>'
		
			RETURNSTR += self.folder_end()
			return RETURNSTR
	    
	
		RETURNSTR += self.printdir(dir)
		return RETURNSTR
	
	def cleanPath(self,f):
		return f.replace(self.strDSEP+self.strDSEP,self.strDSEP)
	
	def isdir(self,f,t):
		f = str(f)
		if self.mode == 'local':
			return os.path.isdir(f)
		return int(t) == 4
		
	def basename(self,b):
		b = str(b)
		if self.strDSEP == '/':
			return re.sub('.*'+self.strDSEP,'',b)
		else:
			return re.sub('.*'+'\\\\','',b)
    
	def folder_file(self,f):
		f = str(f)
		return "<li class=\"file file_"+re.sub('^.*\.','',f.lower())+" vboxListItem\"><a href=\"#\" name='"+f+"' rel=\""+f+"\">"+self.basename(f)+"</a></li>\n"
    
	def folder_folder(self,f,full=False,expanded=False,selected=False):
		f = str(f)
		return "<li class=\"directory "+('expanded' if expanded else 'collapsed')+" vboxListItem"+('Selected' if selected else '')+"\"><a href=\"#\" name='"+f+"' rel=\""+f+"\">"+(f if full else self.basename(f))+"</a>"+('' if expanded else '</li>')+"\n"
    
    
	def folder_start(self): return "<ul class=\"jqueryFileTree\" style=\"display: none;\">\n"
	def folder_end(self): return "</ul>\n"

	
	def printdir(self,dir,recurse=[]):
                        
		if dir[:-1] != '\\' and dir[:-1] != '/': dir += self.strDSEP;
		
		dir = dir.replace(self.strDSEP+self.strDSEP,self.strDSEP)
		    	
	
		if self.mode != 'local':
			
			appl = self.vbox.createAppliance()
			vfs = appl.createVFSExplorer('file://'+dir)
			progress = vfs.update()
			progress.waitForCompletion(-1)
			progress.releaseRemote()
			files, rtypes = vfs.entryList()
			vfs.releaseRemote()
			appl.releaseRemote()
		
			files = list(files)
			rtypes = list(rtypes)
						
			# Keep files / types association
			ftypes = {}
			for i in range(len(files)):
				files[i] = str(files[i])
				ftypes[str(files[i])] = int(rtypes[i])
			
			rtypes = None
			files.sort()

		else: # local mode
			if not os.path.exists(dir):
				return ''
			files = os.listdir(dir)
			files.sort()
			ftypes = {}
		
		try: files.remove('.')
		except: pass
		try: files.remove('..')
		except: pass
		
		if len(files) == 0: return ''
					        

        # return string
		RSTR = ''
        
		RSTR += self.folder_start()
    
    	# All dirs
		for file in files:
    		
			ftype = ftypes.get(file)
    		
			file = dir + self.strDSEP + file
			
			file = self.cleanPath(file)
			
			if os.path.exists(file) and self.isdir(file,ftype):
				if len(recurse) > 1 and (recurse[0].lower() == self.basename(file).lower()):
					RSTR += self.folder_folder(file,False,True)
					RSTR += self.printdir(dir + self.strDSEP + recurse.pop(0),recurse)
					RSTR +='</li>'    				
				elif len(recurse) == 1 and (recurse[0].lower() == self.basename(file).lower()):
					RSTR += self.folder_folder(file,False,False,True)
				else:
					RSTR += self.folder_folder(file)
    			

		# Files as well?
		if not self.dirsOnly:
    		
    		# All files
			for file in files:
    			
				ftype = ftypes.get(file)
    			
				file = dir + self.strDSEP + file
				
				file = self.cleanPath(file)
    			
				if os.path.exists(file) and (not self.isdir(file,ftype)):

					ext = re.sub('^.*\.', '', file).lower()
    
					if len(self.allowedFiles) and not self.allowedFiles.get('.'+ext):
						continue
    				
					RSTR += self.folder_file(file)

		RSTR += self.folder_end()
		
		return RSTR



