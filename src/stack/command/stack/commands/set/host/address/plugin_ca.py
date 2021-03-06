# @SI_Copyright@
#                             www.stacki.com
#                                  v3.0
# 
#      Copyright (c) 2006 - 2015 StackIQ Inc. All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#  
# 1. Redistributions of source code must retain the above copyright
# notice, this list of conditions and the following disclaimer.
#  
# 2. Redistributions in binary form must reproduce the above copyright
# notice unmodified and in its entirety, this list of conditions and the
# following disclaimer in the documentation and/or other materials provided 
# with the distribution.
#  
# 3. All advertising and press materials, printed or electronic, mentioning
# features or use of this software must display the following acknowledgement: 
# 
# 	 "This product includes software developed by StackIQ" 
#  
# 4. Except as permitted for the purposes of acknowledgment in paragraph 3,
# neither the name or logo of this software nor the names of its
# authors may be used to endorse or promote products derived from this
# software without specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY STACKIQ AND CONTRIBUTORS ``AS IS''
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
# THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL STACKIQ OR CONTRIBUTORS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
# OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN
# IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
# @SI_Copyright@
#
# @Copyright@
#  				Rocks(r)
#  		         www.rocksclusters.org
#  		         version 5.4 (Maverick)
#  
# Copyright (c) 2000 - 2010 The Regents of the University of California.
# All rights reserved.	
#  
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#  
# 1. Redistributions of source code must retain the above copyright
# notice, this list of conditions and the following disclaimer.
#  
# 2. Redistributions in binary form must reproduce the above copyright
# notice unmodified and in its entirety, this list of conditions and the
# following disclaimer in the documentation and/or other materials provided 
# with the distribution.
#  
# 3. All advertising and press materials, printed or electronic, mentioning
# features or use of this software must display the following acknowledgement: 
#  
# 	"This product includes software developed by the Rocks(r)
# 	Cluster Group at the San Diego Supercomputer Center at the
# 	University of California, San Diego and its contributors."
# 
# 4. Except as permitted for the purposes of acknowledgment in paragraph 3,
# neither the name or logo of this software nor the names of its
# authors may be used to endorse or promote products derived from this
# software without specific prior written permission.  The name of the
# software includes the following terms, and any derivatives thereof:
# "Rocks", "Rocks Clusters", and "Avalanche Installer".  For licensing of 
# the associated name, interested parties should contact Technology 
# Transfer & Intellectual Property Services, University of California, 
# San Diego, 9500 Gilman Drive, Mail Code 0910, La Jolla, CA 92093-0910, 
# Ph: (858) 534-5815, FAX: (858) 534-7345, E-MAIL:invent@ucsd.edu
#  
# THIS SOFTWARE IS PROVIDED BY THE REGENTS AND CONTRIBUTORS ``AS IS''
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
# THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE REGENTS OR CONTRIBUTORS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
# OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN
# IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
# @Copyright@
#
# $Log:$
#

from __future__ import print_function
import os
import stack.commands

class Plugin(stack.commands.Plugin):

	def provides(self):
		return 'ca'


	def run(self, args):
		(oldhost, oldip, password) = args

		shortname = self.owner.db.getHostAttr('localhost',
			'Kickstart_PrivateHostname')
		domainname = self.owner.db.getHostAttr('localhost',
			'Kickstart_PublicDNSDomain')

		print('Updating CA certificates')

		newfile = []

		file = open('/etc/security/ca/ca.cfg', 'r')
		for line in file.readlines():
			if line[0:len('commonName_default')] == \
					'commonName_default':
				newfile.append('commonName_default = %s.%s' %
					(shortname, domainname))
			else:
				newfile.append(line[:-1])
		file.close()

		file = open('/tmp/ca.cfg', 'w+')
		file.write('\n'.join(newfile))
		file.write('\n')
		file.close()

		os.system('/bin/mv /tmp/ca.cfg /etc/security/ca/ca.cfg')
		os.system('/bin/chmod 500 /etc/security/ca/ca.cfg')

		#
		# make a new cert
		#
		cmd = 'cd /etc/security/ca; '
		cmd += '/usr/bin/openssl req -new -x509 -extensions v3_ca '
		cmd += '-nodes -keyout ca.key -days 5000 -batch '
		cmd += '-config ca.cfg > ca.crt 2> /dev/null; '
		cmd += 'chmod 0400 ca.key; '
		cmd += 'chmod 0444 ca.crt; '
		os.system(cmd)

		#
		# update the httpd certs
		#
		os.system('cp /etc/security/ca/ca.crt /etc/httpd/conf/ssl.ca/')
		os.system('make -C /etc/httpd/conf/ssl.ca > /dev/null 2>&1')

		#
		# Make a Certificate for Mod_SSL
		#
		cmd = 'cd /etc/pki/tls ; '
		cmd += '/usr/bin/openssl req -new -nodes -config '
		cmd += '/etc/security/ca/ca.cfg -keyout private/localhost.key '
		cmd += ' -subj "'
		cmd += '/C=%s/ ' % self.owner.db.getHostAttr('localhost',
			'Info_CertificateCountry')
		cmd += 'ST=%s/ ' % self.owner.db.getHostAttr('localhost',
			'Info_CertificateState')
		cmd += 'L=%s/ ' % self.owner.db.getHostAttr('localhost',
			'Info_CertificateLocality')
		cmd += 'O=%s/ ' % self.owner.db.getHostAttr('localhost',
			'Info_CertificateOrganization')
		cmd += 'OU=%s/ ' % self.owner.db.getHostAttr('localhost',
			'Kickstart_PrivateHostname')
		cmd += 'CN=%s.%s" ' % (shortname, domainname)
		cmd += '> certs/localhost.csr 2> /dev/null ; '
		cmd += 'chmod 0400 private/localhost.key'
		os.system(cmd)

		#
		# Sign the Request with our CA
		#
		cmd = 'cd /etc/security/ca; '
		cmd += '/usr/bin/openssl x509 -req -days 2000 -CA ca.crt '
		cmd += '-CAkey ca.key -CAserial ca.serial '
        	cmd += '< /etc/pki/tls/certs/localhost.csr '
		cmd += '> /etc/pki/tls/certs/localhost.crt 2> /dev/null ; '
		cmd += 'chmod 0444 /etc/pki/tls/certs/localhost.crt '
		os.system(cmd)

