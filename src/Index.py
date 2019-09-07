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
	detect_path = request.form.get('tpath', None)
	start_detect = request.form.get('start_detect', None)
	
	if start_detect and detect_path:
		level = int(request.form['level'])
		detect_results = detector.detect(detect_path, level)
		for fpath in detect_results:
			detect_item = detect_results[fpath]
			if detect_item:
				size = get_file_size(fpath)
				date = get_file_date(fpath)
				item = {'file': fpath, 'size': size, 'date': date}
				result.append(item)
	return render_template('offline.html', title='离线检测', result=result)
	

@app.route('/realtime', methods = ['GET', 'POST'])
def realtime():
	result = list()
	monitor_path  = request.form.get('tpath', None)
	start_monitor = request.form.get('start', None)
	stop_monitors = request.form.get('stop', None)

	if start_monitor: #增加监控
		level = int(request.form['level'])
		if os.path.isdir(monitor_path):
			if monitor_path not in monitors:
				new_monitor = WebshellMonitor(monitor_path, level)
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
	calc_obj = None

	if not calc_type or not calc_path:
		return render_template('assistant.html', title='辅助检测')

	if calc_type == '重合指数': 
		calc_obj = LanguageIC()
	elif calc_type == '信息熵':
		calc_obj = TextEntropy()
	elif calc_type == '最长字符串':
		calc_obj = LongestWord()
	elif calc_type == '文件压缩比':
		calc_obj = Compression()

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