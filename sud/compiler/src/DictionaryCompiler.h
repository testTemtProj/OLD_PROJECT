#ifndef DICTIONARYCOMPILER_H
#define DICTIONARYCOMPILER_H

#include <QString>
#include <QVector>
#include <QMap>
#include <QFile>

#include <TrieBuilder.h>

class DictionaryCompiler
{
public:
    DictionaryCompiler();
    
    /** Добавляет в словарь определение.
     *
     * \param term          Сама строка определения
     * \param theme_title   Наименование тематики
     * \param rate          Рейтинг определения
     *
     * */
    void AddTerm(const QString &term, const QString &theme_title, int rate); 

    /** Добавляет в словарь произвольные мета-данные. */
    void AddMetaData(const QString &key, const QString &value);
 
    /** Компилирует словарь в файл \a out. Это главный метод, который делает
     * всю работу. */
    void Compile(QFile &out);

    /** Количество тематик в словаре. */
    int GetThemesCount() const
    {
        return theme_to_id_.size();
    }

    /** Количество успешно сохранённых определений. */
    int GetSuccessCount() const
    {
        return success_count_;
    }

    /** Количество пропущенных определений. */
    int GetSkippedCount() const
    {
        return skipped_count_;
    }

    /** Версия компилятора словарей. */
    static const char *Version()
    {
        return "0.3.1";
    }

    /** Название компилятора словарей. */
    static const char *CompilerName()
    {
        return "Suggest Dictionary Compiler";
    }

    static const char end_of_line = '$';
    static const char non_breaking_space = '_';

    bool use_non_breaking_spaces;


private:

    /** Описывает одно словарное определение. */
    struct Entry {
        QString term;
        QString theme_id;
        int rate;

        bool operator<(const Entry &other) const
        {
            return this->term < other.term;
        }
    };

    /** Возвращает id тематики по её заголовку. */
    QString GetThemeId(const QString &theme_title);

    /** Записывает служебные мета-данные. */
    void WriteServiceMetadata();

    /** Компилирует в память все добавленные словарные определения. */
    void CompileEntries();

    /** Компилирует одно определение.
     *
     *  Возвращает false в случае неудачи, например, если не удалось
     *  преобразовать \a entry в кодировку cp1251.
     * */
    bool CompileEntry(const Entry &entry);

    /** Обновляет счётчики узла \a n. */
    void UpdateCounters(BuilderNode *n, const QString &theme, int rate);

    /** Очищает строку от недопустимых символов */
    QString CleanString(const QString &str);

    /** Сортирует словарные определения. */
    void SortEntries();

    /** Расставляет неразрывные пробелы по словарю. Определения должны быть
     *  осортированы перед использованием этой функции. */
    void DetectNonbreakingSpaces();

    QVector<Entry> entries_;
    TrieBuilder builder_;

    QMap<QString, QString> theme_to_id_;
    int themes_count_;
    int success_count_;
    int skipped_count_;

};

#endif
