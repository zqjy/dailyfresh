# dailyfresh
pip freeze > requirements.txt # 生成项目依赖库文件
pip install -r requirements.txt # 加载项目依赖库
pip install isdangerous -i http://pypi.douban.com/simple --trusted-host pypi.douban.com # 安装isdangerous失败时使用
sudo apt-get install libjpeg8 libjpeg62-dev libfreetype6 libfreetype6-dev # ubuntu 下 pillow安装失败执行
pip install Pillow==3.4.1 -i http://pypi.douban.com/simple --trusted-host pypi.douban.com
celery -A celery_tasks.tasks worker -l info
mysql -u root -p dailyfresh < dailyfresh.sql # 导入数据
mysql -u root -p dailyfresh > dailyfresh.sql # 导出数据
\. ~/python/dailyfresh.sql # 执行sql文件
