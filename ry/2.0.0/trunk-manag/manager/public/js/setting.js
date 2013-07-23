Ext.onReady(function() {
    settings = {
        id: 'settings',
        title: 'Рынок',
        layout: 'border',
        border: false,
        items: [
            rynokTree,
            {
                id:'settings-panel',
                xtype:'panel',
                region: 'center',
                layout: 'fit'
            }
        ],
        onLoad: function() {
            initTree();
            initSettings();
        }
    }
})

var rynokTree = new Ext.tree.TreePanel({
    root: new Ext.tree.AsyncTreeNode({
		text: 'Категории Рынка',
		draggable:false,
        editable: false,
		id:'0'
	})
    ,useArrows:true,
    id:'rynok-tree',
    region: 'west',
    width:'20%',
    split: true,
    animate:true,
    autoScroll:true,
    loader: new Ext.tree.TreeLoader({dataUrl:'/category/getYottosTreeSettings'}),
    enableDD:true,
    containerScroll: true,
    rootVisible: true,
    dropConfig: {appendOnly:true},
    tbar: new Ext.Toolbar({
        items:[{
            pressed: false,
            enableToggle:true,
            text: 'Раскрыть все дерево',
            toggleHandler: function(btn, pressed)
            {
                if(pressed)
                {
                    rynokTree.root.eachChild(function(){
                        this.expand()
                    })
                }
                else
                {
                    rynokTree.root.eachChild(function(){
                        this.collapse()
                    })
                }
            }
        }]
    })
});

var campaignCB = []

function initSettings() {
    Ext.Ajax.request({
        url: '/settings/get_settings',
        success: function(data){

            var data = Ext.util.JSON.decode(data.responseText)
            campaignCB = data['categories']

            categoryPositionForm3x3 = new Ext.Panel({
                labelWidth: 100,
                fieldLabel: 'Позиция категорий',
                frame:false,
                bodyStyle:'padding:10px; border: 0px;',
                defaults: {frame:false, bodyStyle: 'border: 0px; font-size: 12px; padding: 5px'},
                labelAlign: 'left',
                layout: {
                    type: 'table',
                    columns: 3
                },
                items: [
                    {html:'', items: [{xtype: 'combo', triggerAction: 'all', id: '3pos1', name: '3pos1', store: campaignCB}]},
                    {html:'', items: [{xtype: 'combo', triggerAction: 'all', id: '3pos2', name: '3pos2', store: campaignCB}]},
                    {html:'', items: [{xtype: 'combo', triggerAction: 'all', id: '3pos3', name: '3pos3', store: campaignCB}]},
                    {html:'', items: [{xtype: 'combo', triggerAction: 'all', id: '3pos4', name: '3pos4', store: campaignCB}]},
                    {html:'', items: [{xtype: 'combo', triggerAction: 'all', id: '3pos5', name: '3pos5', store: campaignCB}]},
                    {html:'', items: [{xtype: 'combo', triggerAction: 'all', id: '3pos6', name: '3pos6', store: campaignCB}]},
                    {html:'', items: [{xtype: 'combo', triggerAction: 'all', id: '3pos7', name: '3pos7', store: campaignCB}]},
                    {html:'', items: [{xtype: 'combo', triggerAction: 'all', id: '3pos8', name: '3pos8', store: campaignCB}]},
                    {html:'', items: [{xtype: 'combo', triggerAction: 'all', id: '3pos9', name: '3pos9', store: campaignCB}]},
                ]
            })

            categoryPositionForm3x2 = new Ext.Panel({
                labelWidth: 100,
                fieldLabel: 'Позиция категорий',
                frame:false,
                bodyStyle:'padding:10px; border: 0px;',
                defaults: {frame:false, bodyStyle: 'border: 0px; font-size: 12px; padding: 5px'},
                labelAlign: 'left',
                layout: {
                    type: 'table',
                    columns: 3
                },
                items: [
                    {html:'', items: [{xtype: 'combo', triggerAction: 'all', id: '2pos1', name: '2pos1',store: campaignCB}]},
                    {html:'', items: [{xtype: 'combo', triggerAction: 'all', id: '2pos2', name: '2pos2',store: campaignCB}]},
                    {html:'', items: [{xtype: 'combo', triggerAction: 'all', id: '2pos3', name: '2pos3',store: campaignCB}]},
                    {html:'', items: [{xtype: 'combo', triggerAction: 'all', id: '2pos4', name: '2pos4',store: campaignCB}]},
                    {html:'', items: [{xtype: 'combo', triggerAction: 'all', id: '2pos5', name: '2pos5',store: campaignCB}]},
                    {html:'', items: [{xtype: 'combo', triggerAction: 'all', id: '2pos6', name: '2pos6',store: campaignCB}]},
                ]
            })

            lineType = new Ext.form.ComboBox({
                fieldLabel: 'Тип вывода категорий',
                name: 'type',
                store: ['3x2', '3x3'],
                value: data['type'],
                editable: false,
                triggerAction: 'all',
            })

            lineType.on('select', function(){
                var value = lineType.getValue()
                if(value == '3x2')
                {
                    categoryPositionForm3x2.setVisible(true)
                    categoryPositionForm3x3.setVisible(false)
                }
                if(value == '3x3')
                {
                    categoryPositionForm3x3.setVisible(true)
                    categoryPositionForm3x2.setVisible(false)
                }

            })

            var colsCatsPopGoods = new Ext.form.ComboBox({
                fieldLabel: 'Кол-во категорий для популярных товаров',
                name: 'colCatsPopGoods',
                store: [1, 2, 3, 4, 5],
                value: data['colCatsPopGoods'],
                editable: true,
                triggerAction: 'all',
            })

            var colsPopGoods = new Ext.form.ComboBox({
                fieldLabel: 'Кол-во товаров для каждой категории',
                name: 'colPopGoods',
                store: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
                value: data['colPopGoods'],
                editable: true,
                triggerAction: 'all',
            })

            var colsCatsNewGoods = new Ext.form.ComboBox({
                fieldLabel: 'Кол-во категорий для популярных товаров',
                name: 'colsCatsNewGoods',
                store: [1, 2, 3, 4, 5],
                value: data['colsCatsNewGoods'],
                editable: true,
                triggerAction: 'all',
            })

            var colsNewGoods = new Ext.form.ComboBox({
                fieldLabel: 'Кол-во товаров',
                name: 'colsNewGoods',
                store: [10, 20, 50, 100],
                value: data['colsNewGoods'],
                editable: true,
                triggerAction: 'all',
            })

            var baner = new Ext.form.TextArea({
                fieldLabel: 'Баннер',
                name: 'baner',
                value: data['baner'],
                height: 200,
                anchor: '100%'
            })

            var mainPageForm = new Ext.FormPanel({
                url:'settings/save_main_page_settings',
                frame: false,
                labelWidth: 130,
                bodyStyle: 'border: 0px',
                items: [
                        lineType,
                        categoryPositionForm3x2,
                        categoryPositionForm3x3,
                        {html: '<b> Популярные товары </b>', colspan: 2, bodyStyle: 'border: 0px; padding: 10px'},
                        colsCatsPopGoods,
                        colsPopGoods,
                        {html: '<b> Новые товары </b>', colspan: 2, bodyStyle: 'border: 0px; padding: 10px'},
                        //colsCatsNewGoods,
                        colsNewGoods,
                        baner
                ]
            });

            var panel = new Ext.Panel({
                labelWidth: 100,
                frame:true,
                width: 210,
                bodyStyle:'padding:0px; border: 0px; font-size: 8px',
                defaults: {frame:false, bodyStyle: 'border: 0px; font-size: 12px; padding: 0px'},
                labelAlign: 'left',
                layout: {
                    type: 'table',
                    columns: 2,
                },
                items: [
                        {html:'Текст:'},{xtype: 'textfield', triggerAction: 'all', name: 'lincText_1'},
                        {html:'Ссылка:'},{xtype: 'textfield', triggerAction: 'all', name: 'linc_1'},

                        ]

            })

            var footerForm = new Ext.Panel({
                    frame:false,
                    defaults: {frame:false, bodyStyle: 'border: 0px; font-size: 12px; padding: 5px'},
                    labelAlign: 'left',
                    layout: {
                        type: 'table',
                        columns: 4
                    },
                    items: []
                })
            for(var i=0; i < 20; i++)
            {
                    var panel = new Ext.Panel({
                    labelWidth: 100,
                    frame:true,
                    width: 210,
                    bodyStyle:'padding:0px; border: 0px; font-size: 8px',
                    defaults: {frame:false, bodyStyle: 'border: 0px; font-size: 12px; padding: 0px'},
                    labelAlign: 'left',
                    layout: {
                        type: 'table',
                        columns: 2,
                    },
                    items: [
                            {html:'Текст:'},{xtype: 'textfield', triggerAction: 'all', name: 'lincText_'+i, id: 'lincText_'+i},
                            {html:'Ссылка:'},{xtype: 'textfield', triggerAction: 'all', name: 'linc_'+i, id: 'linc_'+i},
                            ]

                })
                footerForm.add(panel);
            }
            var productCountPerPageTextField = new Ext.form.TextField({
                fieldLabel:'Кол-во товара на странице',
                editable: true,
                value: data['count'],
                name: 'goodsCount'
            })

            var settingsForm = new Ext.FormPanel({
                url:'settings/save_common_settings',
                labelWidth: 130,
                bodyStyle: 'border: 0px',
                items: [
                        //{fieldLabel:'Корзина', name: 'goods', checked: data['cart'], xtype: 'checkbox'},
                        {fieldLabel:'Вишлист', name: 'vishlist', checked: data['vishlist'], xtype: 'checkbox'},
                        //productCountPerPageTextField,
                        {title:'Настройка Footer'},
                        footerForm]
            })

            var searchForm = new Ext.FormPanel({
                url:'settings/save_search_settings',
                frame: false,
                labelWidth: 130,
                bodyStyle: 'border: 0px',
                items: [{fieldLabel:'Баннер', name: 'baner', xtype: 'textarea', value: data['searchBaner'], anchor: '100%', height: 300}]
            })

            for(var i=0, j=0; i<20; i++)
            {
                linc = ''
                for(r=9;;r++)
                {
                    if(data['fields'][j] && data['fields'][j][r] != '\'')
                    {
                        linc += data['fields'][j][r]
                    }
                    else
                    {
                        break
                    }
                }
                text = '';
                start = false;
                if (data['fields'][j])
                for(r=1; r<data['fields'][j].length; r++)
                {
                    if(data['fields'][j] && data['fields'][j][r] == '>')
                    {
                        start = true
                        continue
                    }
                    if(start == true)
                    {
                        if(data['fields'][j][r] != '<')
                        {
                            text += data['fields'][j][r]
                        }
                        else
                        {
                            break
                        }
                    }
                }
                footerForm.findById('linc_'+i).setValue(linc)
                footerForm.findById('lincText_'+i).setValue(text)
                j++
            }

            var tabs = new Ext.TabPanel({
				activeTab: 0,
                enableTabScroll: true,
                height: 700,
				defaults: { autoScroll: true },
				items: [{
					title: 'Общие настройки',
					id: 'common',
					bodyStyle: 'padding:5px;',
					items: [
						settingsForm,
					],
                    tbar: [
                        {
                            text:'Сохранить'
                            ,id: 'save-common'
                            ,iconCls: 'u-icon-save'
                            ,handler:function() {
                                settingsForm.getForm().submit();
                                var btn = Ext.getCmp('save-common')
                                btn.disable()
                                btn.setText('Сохранено')
                                setTimeout(function(){
                                    btn.enable()
                                    btn.setText('Сохранить')
                                }, 500)
                            }
                        }
                    ]
				},{
					title: 'Главная страница',
					id: 'main',
					bodyStyle: 'padding:5px;',
					items: [
						mainPageForm,
					],
                    tbar: [
                        {
                            text:'Сохранить'
                            ,id: 'save-main'
                            ,iconCls: 'u-icon-save'
                            ,handler:function() {
                                mainPageForm.getForm().submit();
                                var btn = Ext.getCmp('save-main')
                                btn.disable()
                                btn.setText('Сохранено')
                                setTimeout(function(){
                                    btn.enable()
                                    btn.setText('Сохранить')
                                }, 500)
                            }
                        }
                    ]
				},{
					title: 'Страница поиска',
					bodyStyle: 'padding:5px;',
					items: [
						searchForm,
					],
                    tbar: [
                        {
                            text:'Сохранить'
                            ,id: 'save-search'
                            ,iconCls: 'u-icon-save'
                            ,handler:function() {
                                searchForm.getForm().submit();
                                var btn = Ext.getCmp('save-search')
                                btn.disable()
                                btn.setText('Сохранено')
                                setTimeout(function(){
                                    btn.enable()
                                    btn.setText('Сохранить')
                                }, 500)
                            }
                        }
                    ]
				}]
			});

            tabs.on('tabchange', function(obg, tab){
                if(tab.id == 'main')
                {
                    Ext.Ajax.request({
                    url: '/settings/get_settings',
                    success: function(data){
                        var data = Ext.util.JSON.decode(data.responseText)
                        var value = data['type']
                        if(value == '3x2')
                        {
                            categoryPositionForm3x2.setVisible(true)
                            categoryPositionForm3x3.setVisible(false)
                            for(var i=1, j=0; i<7; i++)
                            {
                                categoryPositionForm3x2.findById('2pos'+i).setValue(data['mainFields'][j])
                                j++
                            }

                        }
                        if(value == '3x3')
                        {
                            categoryPositionForm3x3.setVisible(true)
                            categoryPositionForm3x2.setVisible(false)
                            for(var i=1, j=0; i<10; i++)
                            {
                                categoryPositionForm3x3.findById('3pos'+i).setValue(data['mainFields'][j])
                                j++
                            }
                        }
                    }
                    });
                }
            })
            
            var settingsPanel = Ext.getCmp('settings-panel')
            settingsPanel.update('')
            tabs.applyToMarkup(settingsPanel.body.id)
        }
    })
}
