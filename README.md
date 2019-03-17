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

/usr/bin/fdfs_trackerd /etc/fdfs/tracker.conf start  # 开启tracker
/usr/bin/fdfs_storaged /etc/fdfs/storage.conf start  # 开启storage
fdfs_upload_file /etc/fdfs/client.conf cat.jpg  # 测试fastdfs

sudo vim /usr/local/nginx/conf/nginx.conf # nginx返回静态首页配置
location /static {
    alias /home/python/Desktop/dailyfresh/static/;
}
location / {
    root /home/python/Desktop/dailyfresh/static/;
    index  index.html  index.htm;
}

sudo /usr/local/nginx/sbin/nginx   # 开启nginx
sudo /usr/local/nginx/sbin/nginx -s reload # 重启nginx
sudo apt-get install libpcre3 libpcre3-dev # 安装nginx 报错pcre
tar -xvzf zlib-1.2.11.tar.gz # 安装nginx报错zlib
cd zlib-1.2.11
./configure --prefix=/usr/local
make
sudo make install

sudo redis-server /usr/local/redis/redis.conf 

python manage.py rebuild_index # 创建索引
