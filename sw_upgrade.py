import argparse
import os, sys, re
from getpass import getpass
from jnpr.junos import Device

JUNOSDIR = '/usr/local/junos'
PACKAGEDIR = JUNOSDIR + '/packages'
LOGDIR = JUNOSDIR + '/log'

def die(message, errno=1):
  sys.stderr.write("ERROR:{}\n".format(message))
  sys.exit(errno)

##### -------------------------------------------------------------------------
##### CLI args processing
##### -------------------------------------------------------------------------

def cli_args():
  p = argparse.ArgumentParser(add_help=True)

  ### -------------------------------------------------------------------------
  ### login
  ### -------------------------------------------------------------------------

  p.add_argument('hostname', nargs='?', 
    help='hostname or ipaddr')

  p.add_argument('-u','--user', default=os.getenv('USER'),
    help='login user name, defaults to $USER')

  p.add_argument('-P','--passwd', default='',
    help='login user password, defaults assumes ssh-keys')

  p.add_argument('-k', action='store_true', default=False,
    dest='passwd_prompt', 
    help='prompt for user password')

  ### -------------------------------------------------------------------------
  ### softawre
  ### -------------------------------------------------------------------------

  p.add_argument('-v','--version',
    help="Junos version string for checking device facts")

  p.add_argument('-p','--package',
    help='Junos package file')

  ### -------------------------------------------------------------------------
  ###  modes/flags/etc.
  ### -------------------------------------------------------------------------

  p.add_argument('--dry-run', dest='dry_run_mode', action='store_true',
    help='Check for need to upgrade, but do not do it')

  args = p.parse_args()
  if args.passwd_prompt is True: args.passwd = getpass()

  if args.version is None:
    # extract from package file
    m = re.search('-([^\\-]*)-domestic.*',args.package)
    args.version = m.group(1)

  if args.version is None:
    die("No version-string")

  return args

##### -------------------------------------------------------------------------
##### software upgrade process
##### -------------------------------------------------------------------------

def update_my_progress(dev, report):
  print "{}: {}".format(args.hostname, report)

def do_sw_upgrade(dev):
  from jnpr.junos.utils.sw import SW 
  sw = SW(dev)
  ok = sw.install(args.package, progress=update_my_progress)
  if ok is not True:
    die("Unable to install software")

  print "all done, rebooting device ..."
  rsp = sw.reboot()  

##### -------------------------------------------------------------------------
##### MAIN
##### -------------------------------------------------------------------------

args = cli_args()
dev = Device(args.hostname, user=args.user, password=args.passwd)
try:
  print "{}@{} connecting ...".format(args.user,args.hostname)
  dev.open()
except:
  die("Unable to connect to device: {}".format(args.hostname))

has_ver = dev.facts['version']
should_ver = args.version
need_upgrade = bool(has_ver != should_ver)
y_n = ('no','yes')[need_upgrade].upper()
print "UPGRADE={}::HAS:{} == SHOULD:{}".format(y_n,has_ver, should_ver)

if args.dry_run_mode is True:
  dev.close()
  sys.exit(0)

if need_upgrade is False:
  dev.close()
  sys.exit(0)

do_sw_upgrade(dev)
dev.close()