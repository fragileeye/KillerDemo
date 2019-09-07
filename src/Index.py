#coding: utf-8
import os
import time
from flask import Flask, render_template, request
from WebshellMonitor  import WebshellMonitor
from WebshellDetector import WebshellDetector
from WebshellObserver import LanguageIC, TextEntropy, LongestWord, Compression 

app = Flask(__name__, template_folder = r'../templates', static_folder=r'../static')
detector = WebshellDetector(r'../Config', r'../Log')
monitors = dict() #key is the monitored directory, value is a  instance of WebshellMonitor
observer = {'重合指数': LanguageIC(), '信息熵': TextEntropy(), 
			'最长字符串': LongestWord(), '文件压缩比': Compression()}

def get_file_size(fpath):
	fsize = os.path.getsize(fpath)
	fsize = round(fsize/1024, 3)
	return fsize

def get_file_date(fpath):
	local_time = time.localtime(os.path.getctime(fpath))
	format_time = time.strftime('%Y-%m-%d %H:%M', local_time)
	return format_time

@app.route('/')
def index():
	return render_template('index.html')
	
@app.route('/offline', methods = ['GET', 'POST'])
def offline():
	result = list()
	valid_param  = False
	detect_path  = request.form.get('tpath', None)
	detect_flag  = request.form.get('start', None)
	detect_level = request.form.get('level', None)
	
	if detect_flag and detect_path and detect_level:
		if os.path.exists(detect_path): 
			valid_param = True
			
	if valid_param:
		try:
			detect_level = int(detect_level)
		except:
			detect_level = 1
		detect_results = detector.detect(detect_path, detect_level)
		for f in detect_results:
			detect_item = detect_results[f]
			if detect_item:
				size = get_file_size(f)
				date = get_file_date(f)
				item = {'file': f, 'size': size, 'date': date}
				result.append(item)
	return render_template('offline.html', title='离线检测', result=result)
	

@app.route('/realtime', methods = ['GET', 'POST'])
def realtime():
	result = list()
	monitor_path  = request.form.get('tpath', None)
	monitor_level = request.form.get('level', None)
	start_monitor = request.form.get('start', None)
	stop_monitors = request.form.get('stop', None)
	
	if start_monitor: #增加监控
		try:
			monitor_level = int(monitor_level)
		except:
			monitor_level = 1
		if os.path.isdir(monitor_path):
			if monitor_path not in monitors:
				new_monitor = WebshellMonitor(monitor_path, monitor_level)
				new_monitor.start()		
				monitors[monitor_path] = new_monitor
	elif stop_monitors: #关闭监控
		monitor_items = [dpath for dpath in monitors]
		for dpath in monitor_items:
			if request.form.get(dpath, None):
				monitor = monitors[dpath]
				monitor.stop()
				monitors.pop(dpath)
	result.extend([dpath for dpath in monitors])
	return render_template('realtime.html', title='实时检测', result=result)	
	
@app.route('/assistant', methods = ['GET', 'POST'])
def assistant():
	result = list()
	calc_type = request.form.get('calc_type', None)
	calc_path = request.form.get('tpath', None)
	valid_param = False

	if calc_type and calc_path:
		if calc_type in observer and os.path.exists(calc_path):
			valid_param = True
	
	if not valid_param:
		return render_template('assistant.html', title='辅助检测')
	
	calc_obj = observer[calc_type]
	
	if os.path.isfile(calc_path):
		value = calc_obj.calc_from_file(calc_path)
		size = get_file_size(calc_path)
		date = get_file_date(calc_path)
		item = {'value': value, 'file': calc_path, 'size': size, 'date': date}
		result.append(item)
	else:
		#重合指数需要逆序输出，值越小可疑度越高
		if calc_type == "重合指数": 
			reverse_order = False
		else:
			reverse_order = True
		calc_obj.calc_from_directory(calc_path)
		for f, v in calc_obj.sorted_list:
			size = get_file_size(f)
			date = get_file_date(f)
			item = {'value': v, 'file': f, 'size': size, 'date': date}
			result.append(item)
			
	return render_template('assistant.html', title='辅助检测', result=result, calc_type=calc_type)
	
@app.errorhandler
def error():
	return render_template('error.html')

if __name__ == '__main__':
	app.run(debug=True)