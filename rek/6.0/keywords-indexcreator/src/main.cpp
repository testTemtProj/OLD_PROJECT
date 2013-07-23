#include <glog/logging.h>
#include "IndexCreatorService.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <sys/time.h>
#include <sys/wait.h>
#include <unistd.h>
#include <errno.h>
#include <fcntl.h>
#include <syslog.h>
#include <signal.h>
#include <execinfo.h> 
#include <syslog.h>



void SetPidFile(const char * Filename, pid_t pid);

 
#define PID_FILE "/var/run/indexator.pid"


/** \mainpage KeywordsIndexCreator service
 
    \section usage_section �������������

    \b keywords_indexcreator --- ��� ������, ������������� �� ���������� � ����������
	������� ���������� ��������������� ������ CLucene. 

	������ �������� ������� �����������, ����������� ��� ������ �� /etc/init.d

    ������� ������������� �� ��������� ������ (indexator.conf - ���� ������������, ��. ����):

    \code
	keywords_indexcreator indexator.conf
    \endcode


    \section settings_section ��������� �������

    keywords_indexcreator ��� ���������� ������� ���������� ���� ������ mongo, 
	������� �������� �������� ���� ��������� �����������. ��� �������� ���� ������ �������,
       ������� ���������� ���������������� �����. �� ������ ����������
       �������������� ��� ���� ������ �� ��������� (��. DB::addDatabase).


    ��������� ����������� � ���� ������ �������� � ����� ������������.
	��������� \c mongo_main_host, \c mongo_main_db �������� ����� (� �������
    "host[:port]" � �������� ��� ������. 

    �� ��������� ����� ������������ ��������� ���������:

    \code
	mongo_main_host = localhost
	mongo_main_db = getmyad_db
	mongo_main_set = ''
	mongo_main_slave_ok = false
    \endcode

	����� ����, � ����� ������������ �������� ���������� \c index_folder, ���������� �� 
	����� ���������� ������� �� ���������� �����.

	�� ��������� ����� ������������ ��������� ���������:

    \code
	index_folder = /var/www/index
    \endcode

	������ ����������������� �����:

    \code
	mongo_main_host=213.186.119.121:27017,213.186.119.121:27018,213.186.119.121:27019
	mongo_main_set=vsrv
	mongo_main_db=getmyad_db
	mongo_main_slave_ok=true
	index_folder=/var/www/index
    \endcode


*/
int main(int argc, char *argv[])
{
    google::InitGoogleLogging(argv[0]);
    //printf("%s",argv[1]);
	if (argc ==1) { printf ("Configuration file is needed!\nProcess stoped.....\n"); return 0;}

    pid_t parpid, sid;
    
    parpid = fork(); //������� �������� �������
    //The parent process should get a non-zero pid from fork
    //The child process should get 0

    if (parpid < 0) //negative indicates error
    {
        printf("Error: Start Daemon failed (%s)\n", strerror(errno));
        exit(EXIT_FAILURE);
    } 
    else if (parpid > 0) //parent process, exit success
    {
        printf("Demon starting... ");
	 	
    	SetPidFile(PID_FILE, parpid);	

        exit(EXIT_SUCCESS);
    }

    umask(0);//���� ����� �� ������ � ��
    sid = setsid();

    if(sid < 0)
    {
	printf("sid<0\n");
        exit(EXIT_FAILURE);
    }

    if((chdir("/")) < 0) {//������� � tmp
	exit(EXIT_FAILURE);
	}
	close(STDIN_FILENO);
	open("/dev/null",O_RDONLY); 
	close(STDOUT_FILENO);
	open("/dev/null",O_WRONLY);
	close(STDERR_FILENO);
	dup(1);

	return IndexCreatorService(argv[1]).Serve();
}


/**
������� �������� ����� � PID'�� ��������
*/
void SetPidFile(const char* Filename, pid_t pid)
{
    FILE* f;
    f = fopen(Filename, "w+");
    if (f)
    {
        fprintf(f, "%u", pid);
        fclose(f);
    }
}



