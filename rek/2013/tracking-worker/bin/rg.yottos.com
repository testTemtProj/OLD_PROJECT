<VirtualHost *:80>
	DocumentRoot /var/www/rg.yottos.com/
	ErrorLog /var/log/apache2/ERROR.rg.yottos.com.log
    CustomLog /var/log/apache2/ACCESS.rg.yottos.com.log combined
	ServerName rg.yottos.com
	ServerAlias "*.rg.yottos.com"
	ServerAlias rg.3.3.yottos.com
	ServerAlias rg.3.2.yottos.com
	ServerAlias rg.4.yottos.com
    FastCgiServer /var/www/rg.yottos.com/cgi/getmyad-tracking-worker \
        -processes 1 \
        -init-start-delay 1 \
        -restart-delay 6 \
        -idle-timeout 5 \
        -listen-queue-depth 400 \
        -initial-env mongo_main_host=213.186.121.76:27018,213.186.121.199:27018,yottos.com \
        -initial-env mongo_main_set=vsrv \
        -initial-env mongo_main_db=getmyad_db \
        -initial-env mongo_main_slave_ok=true \
        -initial-env mongo_log_host=localhost \
        -initial-env mongo_log_db=getmyad_tracking \
        -initial-env GLOG_logbufsecs=0 \
        -initial-env cookie_unique_id_parameter_name=yottos_unique_id \
        -initial-env cookie_unique_id_domain=.yottos.com \
        -initial-env cookie_tracking_parameter_name=yottos_tracking \
        -initial-env cookie_tracking_domain=.yottos.com \
        -initial-env GLOG_log_dir=/tmp \
        -initial-env GLOG_v=0 
    ScriptAlias /track.fcgi /var/www/rg.yottos.com/cgi/getmyad-tracking-worker
</VirtualHost>
