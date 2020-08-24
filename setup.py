import os
import sys

def kill():
	os.system("ps aux | grep ython | grep subscription_v3 | awk '{print $2}' | xargs kill -9")

def setup(arg = ''):
	kill()
	if 'kill' in sys.argv:
		return 
	
	addtional_arg = ' '.join(sys.argv[1:])
	command = 'python3 -u subscription_v3.py %s' % addtional_arg
	if 'debug' in addtional_arg or 'skip' in addtional_arg or 'once' in addtional_arg:
		os.system(command + ' test')
	else:
		os.system('nohup %s &' % command)
		if 'notail' not in addtional_arg:
			os.system('touch nohup.out && tail -F nohup.out')


if __name__ == '__main__':
	setup()