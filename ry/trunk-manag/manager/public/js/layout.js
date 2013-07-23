/*!
 * Ext JS Library 3.3.1
 * Copyright(c) 2006-2010 Sencha Inc.
 * licensing@sencha.com
 * http://www.sencha.com/license
 */

Ext.onReady(function() {
	Ext.QuickTips.init();
    
    var viewport = new Ext.Viewport({
        layout:'border',
        items:[
            {
                cls: 'docs-header',
                height: 34,
                region:'north',
                xtype:'box',
                el:'header',
                border:false,
                margins: '0 0 5 0'
            },
            {
            id: 'main-panel',
            region:'center',
            xtype: 'grouptabpanel',
    		tabWidth: 180,
    		activeGroup: 0,
            initComponent: function() {
                Ext.ux.GroupTabPanel.prototype.initComponent.call(this);
                this.items.each(function(item){
                    item.items.each(function(element){
                        // defaults
                        if(typeof(element.layout) !== 'string')
                            element.layout = 'fit'

                        if(typeof(element.iconCls) !== 'string')
                            element.iconCls = 'x-icon-' + element.id

                        if(typeof(element.style) !== 'string')
                            element.style = 'padding: 10px;'
                        
                        // event
                        item.on('tabchange', function(current){
                            if(current.activeTab.id == element.id) {
                                clearInterval(window.updateInterval);
                                if(element.onLoad !== undefined) {
                                    element.onLoad()
                                }
                            }
                        }, this)
                    },this);
                },this);
            },
    		items: [{
    			mainItem: 0,
    			items: [
                    settings,
                    campaigns,
                    categories,
                    {
                        title: 'Статические страницы',
                        iconCls: 'x-icon-templates',
                        tabTip: 'Статические страницы',
                        style: 'padding: 10px;',
                        layout: 'border',
                        items: [
                           static_pages_content_tree,
                           static_pages_content_tabs
                        ]
                    }
                ]
            },{
                items: [
                    {
                        title: 'Парсер',
                        id: 'parser',
                        onLoad: function() {
                            $('#parser .x-panel-body').html('<iframe style="border: 0" border=0 width=100% height=100% src="http://parser.yotos.ru/"></iframe>');
                        }
                    }
                ]
            }
            ]
		}]
    });
    viewport.doLayout();
});
