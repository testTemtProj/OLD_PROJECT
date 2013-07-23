<VirtualHost *:80>
	DocumentRoot /var/www/rg.yottos.com/
	ErrorLog /var/log/apache2/ERROR.rg.yottos.com.log
    CustomLog /var/log/apache2/ACCESS.rg.yottos.com.log combined
	ServerName rg.yottos.com
	ServerAlias "*.rg.yottos.com"
	ServerAlias rg.3.3.yottos.com
	ServerAlias rg.3.2.yottos.com
	ServerAlias rg.4.yottos.com
    FastCgiServer /var/www/rg.yottos.com/cgi/getmyad-worker \
        -processes 4 \
        -init-start-delay 1 \
        -restart-delay 6 \
        -listen-queue-depth 400 \
        -initial-env mongo_main_host=213.186.121.76:27018,213.186.121.199:27018,yottos.com \
        -initial-env mongo_main_set=vsrv \
        -initial-env mongo_main_db=getmyad_db \
        -initial-env mongo_main_slave_ok=true \
        -initial-env mongo_log_host=localhost \
        -initial-env mongo_log_db=getmyad \
        -initial-env GLOG_logbufsecs=0 \
        -initial-env SERVER_ADDR=127.0.0.1 \
        -initial-env redis_short_term_history_host=127.0.0.1 \
        -initial-env redis_short_term_history_port=6380 \
        -initial-env redis_long_term_history_host=127.0.0.1 \
        -initial-env redis_long_term_history_port=6382 \
        -initial-env redis_user_view_history_host=127.0.0.1 \
        -initial-env redis_user_view_history_port=6381 \
        -initial-env redis_page_keywords_host=127.0.0.1 \
        -initial-env redis_page_keywords_port=6383 \
        -initial-env range_query=1 \
        -initial-env range_short_term=0.75 \
        -initial-env range_long_term=0.5 \
        -initial-env range_context=0.8 \
        -initial-env range_context_term=0.70 \
        -initial-env range_on_places=0.01 \
        -initial-env shortterm_expire=3600 \
        -initial-env views_expire=3600 \
        -initial-env context_expire=3600 \
        -initial-env index_folder_offer=/var/www/indexOffer \
        -initial-env index_folder_informer=/var/www/indexInformer \
        -initial-env REDIRECT_SCRIPT_URL=http://rg.yottos.com/redirect \
        -initial-env cookie_parameter_name=yottos_unique_id \
        -initial-env cookie_domain=.yottos.com \
        -initial-env GLOG_log_dir=/tmp \
        -initial-env GLOG_v=0 \
        -initial-env cookie_path=/ 
    ScriptAlias /adshow.fcgi /var/www/rg.yottos.com/cgi/getmyad-worker
</VirtualHost>
