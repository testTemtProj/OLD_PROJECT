#include <iostream>
#include <QFile>
#include <QTime>
#include <QTextStream>
#include <QTextCodec>
#include <QString>
#include <QStringList>

#include <sys/resource.h>
#include <sys/time.h>

#include "DictionaryCompiler.h"

void print_help()
{
    std::cout << DictionaryCompiler::CompilerName() << " "
              << DictionaryCompiler::Version() << "\n"
                 "usage: compiler [--disable-non-breaking-spaces] out_file\n"
                 "reads dictionary entries from stdin (one per line), "
                 "then compiles them to out_file\n"
                 "\n"
                 "Line format:\n"
                 "definition [\\t theme] [\\t int_weight]\n";
}


/** Формат входных данных:

    Каждая строка содержит словарное определение. Опционально, после
    определения могут идти вес и тематика, разделённые табуляцией.

    Можно сохранять произвольные мета-данные, доступные ко ключу. Каждая такая
    запись передаётся во входной поток в следующем формате::

    \metadata ключ
    (данные...)
    (данные...)
    \metadata-end
*/
int main(int argc, char **argv)
{
    if (argc < 2 || argc > 3) {
        print_help();
        return 1;
    }

    QString out_filename;
    bool use_non_breaking_spaces = true;

    switch (argc) {
        case 2:
            out_filename = argv[1];
            break;

        case 3:
            if (QString(argv[1]) != "--disable-non-breaking-spaces") {
                print_help();
                return 1;
            }

            use_non_breaking_spaces = false;
            out_filename = argv[2];
            break;

        default:
            print_help();
            return 1;
    }


    QFile f(out_filename);
    if (!f.open(QIODevice::ReadWrite | QIODevice::Truncate)) {
        std::cout << "Could not open file " << out_filename.toStdString() << std::endl;
        return 2;
    }

    QTime time = QTime::currentTime();

    DictionaryCompiler compiler;
    compiler.use_non_breaking_spaces = use_non_breaking_spaces;
    QTextStream in(stdin);
    in.setCodec(QTextCodec::codecForName("UTF-8"));
    QString line;

    forever {
        line = in.readLine();
        if (line.isNull())
            break;

        if (line.startsWith("\\metadata")) {

            // Пользовательские мета-данные

            QString metadata_key = line.section("\\metadata ", 1, 1);
            QStringList metadata_value;
            line = in.readLine();
            while (line != "\\metadata-end") {
                metadata_value.append(line);
                line = in.readLine();
            }
            compiler.AddMetaData(metadata_key, metadata_value.join("\n"));
            continue;
        }

        else {

            // Словарное определение

            QStringList row = line.split('\t');
            QString term = row[0];
            QString theme_title = row.value(1).isNull()? "0" : row.at(1);
            bool ok;
            int rate = row.value(2).toInt(&ok);
            if (!ok)
                rate = 1;
            compiler.AddTerm(term, theme_title, rate);
        }
    }

    compiler.Compile(f);

    rusage usage;
    getrusage(RUSAGE_SELF, &usage);
    std::cout << "Time:          " << time.elapsed() << " ms \n"
              << "Resident size: " << usage.ru_maxrss << "K \n"
              << "Terms added:   " << compiler.GetSuccessCount() << "\n"
              << "Terms skipped: " << compiler.GetSkippedCount() << "\n";
    return 0;
}

