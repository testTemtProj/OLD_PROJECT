Template = function(name, data){
    return TrimPath.processDOMTemplate(name, data);
}

String.prototype.highlight = function(search){
    var value = this.toString();
    
    if (search) 
        return value.replace(search, '<span class="term">' + search + '</span>');
    else 
        return value;
}

String.prototype.getExtendedDate = function(a){
    var value = this.toString();
    
    if (value && value.length > 5) {
        var matches = value.match(/([0-9]+)/g);
        return {
            datetime: value,
            timeago: jQuery.timeago(value),
            year: matches[0],
            month: matches[1],
            day: matches[2],
            hour: matches[3],
            min: matches[4],
            sec: matches[5],
            micro: matches[6]
        }
    }
    else {
        return {
            datetime: false
        };
    }
}

var parsing = {}



Ext.EventManager.onDocumentReady(function(){
    Ext.override(Ext.grid.GridView, {
    onLoad:function(){
        updateProgress();
        updateLinks();
    }
});
    function updateLinks() {
        $('a[url]').each(function(){
            var url = $(this).attr('url');
            $(this).attr('href', url);
        })
    }

    function updateProgress(){
        $('.progress').each(function(){
            var id = parseInt($(this).attr('id').replace('progress-', ''));
            if (id > 0) {
                if ($('#progress-bar-' + id).length == 0) {
                    var progressBar = new Ext.ProgressBar({
                        text: 'Обработка',
                        id: 'progress-bar-' + id,
                        renderTo: 'progress-' + id
                    });
                }
                
                var progressBar = Ext.getCmp('progress-bar-' + id);
                var record = store.getById(id);
                var status = record.get('status');
                var progress = 0;
                
                if (status.progress) {
                    if (status.progress.state == 'download_yml') 
                        progress = 0.1;
                    if (status.progress.state == 'parsing_categories') 
                        progress = 0.3;
                    if (status.progress.state == 'parsing_offers') {
                        progress = 0.3;
                        if (status.progress.total > 0) {
                            progress = 0.3 + 0.7 * (status.progress.current / status.progress.total);
                        }
                    }
                }
                
                progressBar.updateProgress(progress);
            }
        })
    }
    
    function getStates(){
        var stack = []
        
        for (market_id in parsing) {
            stack.push(parseInt(market_id));
        }
        
        if (stack.length > 0) 
            $.post('/parser_settings/get_states', {
                markets: stack
            }, function(response){
                for (market_id in response.states) {
                    var rec = store.getById(market_id);
                    if (rec) {
                        rec.set('status', response.states[market_id]['state'])
                        rec.set('started', response.states[market_id]['started'])
                        rec.set('finished', response.states[market_id]['finished'])
                        rec.set('last_update', response.states[market_id]['finished'])
                        rec.set('status_id', response.states[market_id]['status_id'])
                        
                        parsing[market_id] = response.states[market_id]['state'];
                        
                        updateProgress();
                        
                        if (response.states[market_id]['state'].state == 'finished') {
                            delete parsing[market_id];
                        }
                    }
                }
            })
    }

    setInterval(getStates, 500);
    
    var paramsArray = {}
    
    $('.interval').live('click', function(){
        _market_id = $(this).attr('id').replace('interval-market-', '');
        
        var rec = store.getById(_market_id);
        Ext.getCmp('window').show();

        var intervalChoice = Ext.getCmp('interval-choice');
        intervalChoice.setValue(rec.data.time_setting.interval);
        intervalChoice.fireEvent('select');

        var intervalCount = Ext.getCmp('interval-count');
        intervalCount.setValue(rec.data.time_setting.interval_count);
        intervalCount.fireEvent('keyup');

        return false;
    })
    
    $('.action-start').live('click', function(){
        var id = $('td:eq(0)', $(this).closest('tr')).text();
        var rec = store.getById(id);
        var state = {
            state: 'pending'
        };
        parsing[id] = state;
        rec.set('status', state)
        rec.set('status_id', 20)
        Ext.Ajax.request({
            url: '/parser_settings/start_parsing_market',
            params: {
                market_id: id
            }
        });
        return false;
    })
    
    var reader = new Ext.data.JsonReader({
        idProperty: 'id',
        root: 'data',
        totalProperty: 'total',
        fields: [{
            name: 'id'
        }, {
            name: 'file_date'
        }, {
            name: 'date_create'
        }, {
            name: 'title'
        }, {
            name: 'urlMarket'
        }, {
            name: 'urlExport'
        }, {
            name: 'last_update'
        }, {
            name: 'time_setting'
        }, {
            name: 'status'
        }, {
            name: 'interval'
        }, {
            name: 'status_id'
        }, {
            name: 'categories_count'
        }, {
            name: 'offers_count'
        }, {
            name: 'started'
        }, {
            name: 'finished'
        }, {
            name: 'delta'
        }]
    });
    
    var store = new Ext.data.GroupingStore({
        url: '/parser_settings/get_markets',
        autoDestroy: true,
        reader: reader,
        sortInfo: {
            field: 'id',
            direction: 'DESC'
        },
        remoteSort: true,
        remoteGroup: true
    })
    store.baseParams.start=0;
    store.load();
    
    var grid = new Ext.grid.GridPanel({
        store: store,
        view: new Ext.grid.GroupingView({
            forceFit: true,
            showGroupName: false,
            enableNoGroups: false,
            enableGroupingMenu: true,
            hideGroupedColumn: false,
            groupTextTpl: '{text} ({[values.rs.length]} {[values.rs.length > 1 ? "магазинов" : "магазин"]})'
        }),
        autoWidth: true,
        viewConfig: {
            forceFit: true
        },
        colModel: new Ext.grid.ColumnModel({
            defaults: {
                sortable: true,
                menuDisabled: true
            },
            columns: [{
                header: 'ID',
                width: 20,
                sortable: true,
                dataIndex: 'id',
                renderer: function(value, metaData, record, rowIndex, colIndex, store){
                    var term = store.baseParams.pattern;
                    return value.toString().highlight(term);
                }
            }, {
                id: 'title',
                header: 'Название магазина',
                width: 150,
                sortable: true,
                dataIndex: 'title',
                renderer: function(value, metaData, record, rowIndex, colIndex, store){
                    var term = store.baseParams.pattern;
                    var url = record.get('urlMarket');
                    if (url.search('http://') == -1) {
                        url = 'http://' + url;
                    }
                    var file_date = record.get('file_date').toString().getExtendedDate();
                    var result = Template("cell-title", {
                        title: value || record.get('urlMarket').replace('http://', '').highlight(term),
                        file_date: file_date.day?file_date:record.get('date_create').toString().getExtendedDate(),
                        market_url: record.get('urlMarket'),
                        market_url_text: record.get('urlMarket').highlight(term),
                        export_url: record.get('urlExport'),
                        export_url_text: record.get('urlExport').highlight(term),
                        categories_count: record.get('categories_count'),
                        offers_count: record.get('offers_count')
                    });
                    
                    return result;
                }
            }, {
                header: 'Последнее обновление',
                width: 50,
                sortable: true,
                dataIndex: 'last_update',
                renderer: function(value, metaData, record, rowIndex, colIndex, store){
                    var data = {
                        started: record.get('started').toString().getExtendedDate(),
                        finished: record.get('finished').toString().getExtendedDate(),
                        total: record.get('delta')
                    }
                    return Template("format-time-ago", data)
                }
            }, {
                header: 'Частота обновления',
                width: 50,
                sortable: true,
                dataIndex: 'interval',
                renderer: function(value, metaData, record, rowIndex, colIndex, store){
                    var value = record.get('time_setting');
                    function getSuffix(min, max, count){
                        if (count > 1 && count < 5) 
                            return max
                        else 
                            return min
                    }
                    var result;
                    if (!value || value.interval=='никогда')
                        result = '<span class="error">никогда</span>';
                    else {
                        result = '<em>' + value.interval_count + ' ' + getSuffix('раз', 'раза', value.interval_count) + ' в ' + value.interval + '</em>';
                        if (value['interval'] != 'час') {
                            for (paramKey in value.Params) {
                                if (paramKey > 0) {
                                    result += '; ';
                                    if (value['interval'] != 'день') {
                                        result += '<br>';
                                    }
                                    if (paramKey%3==0)
                                        result += '<br>';
                                }
                                if (value.Params[paramKey]['date']) {
                                    var s = ''
                                    switch (value.Params[paramKey]['date']['month'])
                                    {
                                        case 1: s="января"; break;
                                        case 2: s="февраля"; break;
                                        case 3: s="марта"; break;
                                        case 4: s="апреля"; break;
                                        case 5: s="мая"; break;
                                        case 6: s="июня"; break;
                                        case 7: s="июля"; break;
                                        case 8: s="августа"; break;
                                        case 9: s="сентября"; break;
                                        case 10: s="октября"; break;
                                        case 11: s="ноября"; break;
                                        case 12: s="декабря"; break;
                                    }
                                    result += value.Params[paramKey]['date']['day']+'-го '+s+' в ';
                                }
                                if (value.Params[paramKey]['day']) {
                                    result += value.Params[paramKey]['day']+'-го в ';
                                }
                                if (value.Params[paramKey]['dayOfWeak']) {
                                    result += value.Params[paramKey]['dayOfWeak']+' в ';
                                }
                                if (value.Params[paramKey]['time']) {
                                    result += value.Params[paramKey]['time'];
                                }
                            }
                        }
                    }
                    var market_id = store.getAt(rowIndex).get('id');
                    return '<a id="interval-market-' + market_id + '" class="interval" href="#">' + result + '</a>'
                }
            }, {
                header: 'Состояние',
                sortable: true,
                id: 'status',
                width: 200,
                dataIndex: 'status_id',
                renderer: function(value, metaData, record, rowIndex, colIndex, store){
                    var value = record.get('status');
                    var market_id = record.get('id');
                    if (!value.progress) 
                        value.progress = false;
                    if (!value.message) 
                        value.message = 'Ошибка';
                    if (!value.code) 
                        value.code = false;
                    if (!value.index) 
                        value.index = market_id;
                    if (value.state == 'pending') 
                        value.state = 'parsing';
                    if (value.state == 'parsing') {
                        parsing[market_id] = value;
                    }
                    return Template('cell-status', value);
                },
                groupRenderer: function(value, metaData, record, rowIndex, colIndex, store){
                    var value = record.get('status')
                    return Template('group-status', value);
                }
            }, {
                header: 'Запустить',
                sortable: true,
                id: 'action',
                width: 20,
                dataIndex: 'status_id',
                renderer: function(value, metaData, record, rowIndex, colIndex, store){
                    return Template('cell-action', {
                        state: value
                    });
                }
            }]
        }),
        sm: new Ext.grid.RowSelectionModel({
            singleSelect: true
        }),
        region: 'center',
        iconCls: 'icon-grid',
        loadMask: false,
        tbar: new Ext.Toolbar({
            items: [{
                text: 'Поиск магазина:',
                xtype: 'label'
            }, {
                xtype: 'tbseparator'
            }, {
                xtype: 'textfield',
                fieldLabel: 'Search',
                name: 'pattern',
                id: 'pattern',
                listeners: {
                    'render': function(c){
                        c.getEl().on('keypress', function(e){
                            if (e.getKey() == e.ENTER) {
                                store.baseParams.pattern = document.getElementById('pattern').value;
                                store.load();
                            }
                        });
                    }
                }
            }, '-', new Ext.PagingToolbar({
                id: 'paging-toolbar',
                pageSize: 20,
                store: store,
                hideBorders: true,
                displayInfo: true,
                beforePageText: 'Страница',
                emptyMsg: 'Не найдено ни одного магазина',
                afterPageText: ' из {0}',
                displayMsg: ' показано c {0} по {1}, всего: {2}',
                //                    #TODO: при переходе со страниц на страницу в parsing хранятся и собираются все обрабатывающиеся,
                //                    проблема может быть если много магазинов обрабатываются одновременно
                //                    listeners: {
                //                        change: function(self, pageData){
                //                            parsing = {}
                //                            return true;
                //                        }
                //                    },
                items: ['-', {
                    text: 'Показать: ',
                    xtype: 'label'
                }, {
                    xtype: 'combo',
                    triggerAction: 'all',
                    autoSelect: true,
                    width: 50,
                    forceSelection: true,
                    editable: false,
                    lazyRender: true,
                    mode: 'local',
                    value: 20,
                    valueField: 'pageSize',
                    displayField: 'pageSize',
                    store: new Ext.data.ArrayStore({
                        id: 1,
                        fields: ['pageSize'],
                        data: [[20], [50], [100]]
                    }),
                    listeners: {
                        select: function(pageSizeCombo){
                            Ext.getCmp('paging-toolbar').pageSize = pageSizeCombo.value;
                            store.baseParams.limit = pageSizeCombo.value;
                            store.load();
                        }
                    }
                }]
            
            }), '-', {
                text: 'Автообновление',
                xtype: 'label'
            }, {
                id: 'auto-update-time',
                xtype: 'combo',
                triggerAction: 'all',
                autoSelect: true,
                width: 100,
                forceSelection: true,
                editable: false,
                lazyRender: true,
                mode: 'local',
                value: 0,
                valueField: 'interval',
                displayField: 'title',
                store: new Ext.data.ArrayStore({
                    id: 1,
                    fields: ['interval', 'title'],
                    data: [[0, 'отключено'], [600000, 'раз в 10 минут'], [1200000, 'раз в 20 минут'], [36000000, 'раз в 1 час'], [72000000, 'раз в 2 часа'], [360000000, 'раз в 10 часов']]
                }),
                listeners: {
                    select: function(intervalSizeCombo){
                        if (window.updateInterval) 
                            clearInterval(window.updateInterval)
                        
                        if (intervalSizeCombo.value > 0) 
                            window.updateInterval = setInterval(function(){
                                store.reload()
                            }, intervalSizeCombo.value)
                    }
                }
            }, '-', {
                enableToggle: true,
                text: 'Группировать',
                iconCls: 'grouping',
                listeners: {
                    toggle: function(button, pressed){
                        if (pressed) {
                            store.groupBy('status_id');
                        }
                        else {
                            store.clearGrouping();
                        }
                    }
                }
            }, '->', {
                text: 'Выход',
                iconCls: 'parse-close',
                listeners: {
                    click: function(){
                        Ext.Ajax.request({
                            url: '/parser_settings/exit',
                            success: function(res){
                                window.location.href = '/';
                                window.event.returnValue = false;
                            }
                        });
                    }
                }
            }]
        })
    });
    
    var viewport = new Ext.Viewport({
        layout: 'border',
        items: [grid]
    })
    
    viewport.doLayout();
    
    var cbMain = new Ext.form.ComboBox({
        id: 'interval-choice',
        fieldLabel: 'Раз в',
        store: ['никогда', 'час', 'день', 'неделю', 'месяц', 'год'],
        value: 'никогда',
        editable: false,
        mode: 'remote',
        forceSelection: true,
        triggerAction: 'all',
        selectOnFocus: true,
        listeners: {
            change: function() {
                processNext();
            }
        }
    })
    
    cbMain.on('select', function(obg, x, r){
        var value = cbMain.getValue()
        if (value == 'год') {
            nfMain.setDisabled(false)
        }
        else 
            if (value == 'месяц') {
                nfMain.setMaxValue(30)
                nfMain.setDisabled(false)
            }
            else 
                if (value == 'неделю') {
                    nfMain.setMaxValue(6)
                    nfMain.setDisabled(false)
                }
                else 
                    if (value == 'день') {
                        nfMain.setMaxValue(23)
                        nfMain.setDisabled(false)
                    }
                    else 
                        if (value == 'час') {
                            nfMain.setDisabled(true)
                            nfMain.setValue(1)
                            paramsArray['interval'] = 'час'
                            paramsArray['interval_count'] = 1
                        }
                        else 
                            if (value == 'никогда') {
                                nfMain.setDisabled(true)
                                paramsArray['interval'] = ''
                                paramsArray['interval_count'] = 0
                            }
            processNext();
    })
    
    var nfMain = new Ext.form.NumberField({
        id: 'interval-count',
        fieldLabel: 'Кол-во раз',
        value: 1,
        disabled: true,
        minValue: 1,
        enableKeyEvents: true,
        listeners: {
            keyup: function(nf, e) {
                processNext();
            }
        }
    })
    
    nfMain.on('change', function(){
        if (nfMain.isValid()) {
            win.buttons[0].setDisabled(false)
            lMain.setVisible(false)
        }
        else {
            win.buttons[0].setDisabled(true)
            lMain.setVisible(true)
        }
    })
    
    var lMain = new Ext.form.Label({
        html: "<p style = 'color: red'>Неверное значение</p>"
    
    })
    
    lMain.setVisible(false)

    var form = new Ext.FormPanel({
        labelWidth: 100,
        frame: false,
        bodyStyle: 'padding:5px 5px 0',
        defaultType: 'textfield',
        labelAlign: 'left',
        items: [cbMain, nfMain, lMain]
    });
    
    var win = new Ext.Window({
        id: 'window',
        width: 350,
        height: 400,
        closeAction: 'hide',
        plain: true,
        items: [form],
        buttons: [{
            text: 'Готово',
            handler: function(){
                var id = window._market_id;
                var tmp = {};
                var params = [];
                var counter = 0;
                if (paramsArray['interval'] != 'час' && paramsArray['interval'] != '') {
                    for (var i = 0; i < window.form2Items.length; i++) {
                        if (window.form2Items[i].type == 'Label') {
                            if(counter>0) params.push(tmp);
                            counter = 0;
                            tmp = {};
                        } else {
                            if(!window.form2Items[i].isValid()) {
                                win.buttons[0].setDisabled(true);
                                return;
                            }
                            if (window.form2Items[i].type == 'DateField') {
                                var dateField = new Date(window.form2Items[i].getValue());
                                tmp['date'] = {
                                    day: dateField.getDate(),
                                    month: dateField.getMonth()+1
                                }
                                counter++;
                            } else if (window.form2Items[i].type == 'TimeField') {
                                tmp['time'] = window.form2Items[i].getValue()
                                counter++;
                            } else if (window.form2Items[i].type == 'NumberField') {
                                tmp['day'] = window.form2Items[i].getValue()
                                counter++;
                            } else if (window.form2Items[i].type == 'ComboBox') {
                                tmp['dayOfWeak'] = window.form2Items[i].getValue()
                                counter++;
                            }
                        }
                    }
                    if(counter>0) params.push(tmp);
                    paramsArray['interval_count'] = params.length;
                }
                
                paramsArray['Params'] = params
                win.remove(win.items.items[1])
                win.hide()
                Ext.Ajax.request({
                    url: '/parser_settings/set_time_settings',
                    params: {
                        params: Ext.util.JSON.encode(paramsArray),
                        market_id: id
                    },
                    success: function(){
                        store.reload();
                    }
                });
            }
        }]
    });

    function checkValues() {
        win.buttons[0].setDisabled(false);
        if(window.form2Items)
            for (var i = 0; i < window.form2Items.length; i++) {
                if (window.form2Items[i].type != 'Label') {
                    if(!window.form2Items[i].isValid()) {
                        win.buttons[0].setDisabled(true);
                    }
                }
            }
    }

    function processNext() {
        if(win.items.items.length > 1)
            win.remove(win.items.items[1]);

        var cbMainValue = cbMain.getValue()
        var nfMainValue = nfMain.getValue()

        paramsArray['interval'] = cbMainValue
        paramsArray['interval_count'] = nfMainValue

        var items = []
        if (cbMainValue == 'год') {
            for (var i = 0; i < nfMainValue; i++) {
                var rec = store.getById(_market_id);

                var day = '';
                var time = '';

                if(rec.data.time_setting.Params[i]) {
                    var d = new Date();
                    var day = rec.data.time_setting.Params[i].date.month + '/' + rec.data.time_setting.Params[i].date.day + '/' + d.getFullYear();
                    var time = rec.data.time_setting.Params[i].time;
                }

                var label = new Ext.form.Label({
                    html: "<p style = 'color: green'>Параметр №" + (i + 1) + '</p>',
                    type: 'Label'
                })
                var cbDay = new Ext.form.DateField({
                    fieldLabel: 'Число',
                    format:'d.m.Y',
                    type: 'DateField',
                    value: day,
                    disableKeyFilter: true,
                    enableKeyEvents: true,
                    listeners:{keyup: checkValues}
                })
                var cbTime = new Ext.form.TimeField({
                    format: 'H:i',
                    fieldLabel: 'Время',
                    type: 'TimeField',
                    value: time,
                    disableKeyFilter: true,
                    enableKeyEvents: true,
                    listeners:{keyup: checkValues}
                })
                items.push(label)
                items.push(cbDay)
                items.push(cbTime)
            }
        }
        else
        if (cbMainValue == 'месяц') {
            for (var i = 0; i < nfMainValue; i++) {
                var rec = store.getById(_market_id);

                var day = '';
                var time = '';
                if(rec.data.time_setting.Params[i]) {
                    var day = rec.data.time_setting.Params[i].day;
                    var time = rec.data.time_setting.Params[i].time;
                }

                var label = new Ext.form.Label({
                    html: "<p style = 'color: green'>Параметр №" + (i + 1) + '</p>',
                    type: 'Label'
                })
                var cbDay = new Ext.form.NumberField({
                    fieldLabel: 'Число',
                    value: 1,
                    maxValue: 31,
                    minValue: 1,
                    type: 'NumberField',
                    value: day,
                    enableKeyEvents: true,
                    allowNegative: false,
                    allowDecimals: false,
                    allowBlank: false,
                    listeners:{keyup: checkValues}
                })
                var cbTime = new Ext.form.TimeField({
                    format: 'H:i',
                    fieldLabel: 'Время',
                    type: 'TimeField',
                    value: time,
                    disableKeyFilter: true,
                    enableKeyEvents: true,
                    allowBlank: false,
                    listeners:{keyup: checkValues}
                })
                items.push(label)
                items.push(cbDay)
                items.push(cbTime)
            }
        }
        else
        if (cbMainValue == 'неделю') {
            for (var i = 0; i < nfMainValue; i++) {
                var rec = store.getById(_market_id);

                var week = '';
                var time = '';
                if(rec.data.time_setting.Params[i]) {
                    var week = rec.data.time_setting.Params[i].dayOfWeak;
                    var time = rec.data.time_setting.Params[i].time;
                }

                var label = new Ext.form.Label({
                    html: "<p style = 'color: green'>Параметр №" + (i + 1) + '</p>',
                    type: 'Label'
                })
                var cbWeakDay = new Ext.form.ComboBox({
                    fieldLabel: 'День недели',
                    store: ['понедельник', 'вторник', 'среда', 'четверг', 'пятница', 'суббота', 'воскресенье'],
                    editable: true,
                    mode: 'remote',
                    forceSelection: true,
                    triggerAction: 'all',
                    selectOnFocus: true,
                    type: 'ComboBox',
                    value: week
                })
                var cbTime = new Ext.form.TimeField({
                    format: 'H:i',
                    fieldLabel: 'Время',
                    type: 'TimeField',
                    value: time,
                    disableKeyFilter: true,
                    enableKeyEvents: true,
                    listeners:{keyup: checkValues}
                })
                items.push(label)
                items.push(cbWeakDay)
                items.push(cbTime)
            }
        }
        else
        if (cbMainValue == 'день') {
            for (var i = 0; i < nfMainValue; i++) {
                var rec = store.getById(_market_id);

                var time = ''
                if(rec.data.time_setting.Params[i])
                    var time = rec.data.time_setting.Params[i].time;
                
                var label = new Ext.form.Label({
                    html: "<p style = 'color: green'>Параметр №" + (i + 1) + '</p>',
                    type: 'Label'
                })
                var cbTime = new Ext.form.TimeField({
                    format: 'H:i',
                    fieldLabel: 'Время',
                    type: 'TimeField',
                    value: time,
                    disableKeyFilter: true,
                    enableKeyEvents: true,
                    listeners:{keyup: checkValues}
                })
                items.push(label)
                items.push(cbTime)
            }
        }
        window.form2Items = items

        var form2 = new Ext.FormPanel({
            labelWidth: 100,
            name: 'form2',
            frame: false,
            bodyStyle: 'padding:5px 5px 0',
            labelAlign: 'left',
            items: items
        });

        win.add(form2)
        win.hide();
        win.show();
        checkValues();
    }
    win.setAutoScroll(true)
});
