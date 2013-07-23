var market_id = 0;

Ext.onReady(function() {
    categories = {
        id: 'categories'
        ,title: 'Сопоставление категорий'
        ,onLoad: function() {
            yottosTreeRoot.reload();
            marketsStore.reload();
        }
        ,layout: 'border'
        ,items: [yottosTree, goalTree, marketsGrid]
    }
})

function applySearchFilter() {
    yottosTreeLoader.baseParams.pattern = document.getElementById('category_search_term').value;
    goalTreeLoader.baseParams.pattern = document.getElementById('category_search_term').value;
    yottosTreeRoot.reload(function(){
        if (yottosTreeLoader.baseParams.pattern)
            yottosTree.expandAll();
            //if(market_id)
            //    goalTreeRoot.reload();
    });
}

var goalTreeLoader = new Ext.tree.TreeLoader({
    dataUrl:'/category/getShopTree'
    ,listeners: {
        beforeload: function(self, node, callback) {
            self.baseParams.filter = Ext.getCmp('search-market').pressed;
        }
    }
})

var goalTreeRoot = new Ext.tree.AsyncTreeNode({
    text: 'Выберите магазин'
    ,draggable: false
    ,disabled: true
    ,leaf: true
    ,loader: goalTreeLoader
    ,id: '0'
    ,dropConfig: {appendOnly:true}
    ,enableDD: true
});

var goalTree = new Ext.tree.TreePanel({
    root: goalTreeRoot
    ,useArrows:true
    ,region:'center'
    ,enableDD:true
    ,autoScroll: true
    ,listeners: {
        beforeappend: function(tree, parent, node) {
            var full_pattern = goalTreeLoader.baseParams.pattern;
            if(full_pattern) {
                var patterns = full_pattern.split(' ');
                for(var patternCounter = 0; patternCounter<patterns.length;patternCounter++) {
                    var pattern = patterns[patternCounter];
                    if (pattern) {
                        var expr = new RegExp('('+pattern+')', 'ig');
                        node.text = node.text.replace(expr, "<span class='highlight'>$1</span>");
                    }
                }
            }
        },
        dblclick: function(node, e) {
            var words = node.attributes.text.split(/([^A-Za-zА-Яа-я])/gi);
            var search = ''
            for (var word_counter=0; word_counter<words.length; word_counter++) {
                var word = words[word_counter];
                if (word.trim().length>2) {
                    if (word_counter>0) search += ' ';
                    search += word.substr(0,word.length-1).trim();
                }
            }
            var patternField = Ext.getCmp('category_search_term');
            patternField.setValue(search);
            applySearchFilter();
        }
    }
    ,tbar:[
        {
            text:'Загрузить с AdLoad'
            ,id: 'download-categories-button'
            ,iconCls: 'u-icon-download'
            ,disabled: true
            ,handler:function() {
                Ext.Ajax.request({
                    url: '/category/update_category_from_market',
                    params: { market_id: market_id},
                    success: function(result){
                        goalTree.disable();
                        buildMarketCategories();
                    }
                });
            }
        },
        '->',
        {
            text:'Сбросить сопоставление'
            ,id: 'reset-market'
            ,iconCls: 'u-icon-reset'
            ,disabled: true
            ,handler:function() {
                Ext.Msg.show({
                   title:'Сбросить все категории для этого магазина?',
                   msg: 'Вы уверены, что хотите сбросить сопоставление категорий?',
                   buttons: Ext.Msg.YESNO,
                   fn: function(button){
                        if (button == 'yes'){
                            goalTree.disable();
                            yottosTree.disable();
                            Ext.Ajax.request({
                                url: '/category/reset_comparisons',
                                params: { market_id: market_id},
                                success: function(result){
                                    buildMarketCategories();
                                    goalTree.enable();
                                    yottosTree.enable();
                                }
                            });
                        }
                   },
                   animEl: 'reset-market',
                   icon: Ext.MessageBox.QUESTION
                });
            }
        },
        {
            text:'Фильтровать поиск'
            ,id: 'search-market'
            ,iconCls: 'u-icon-search'
            ,enableToggle: true
            ,handler:function() {
                goalTreeRoot.reload();
            }
        }
    ]
})

goalTree.on('beforemovenode', function(tree, node, oldParent, newParent, index) {
    if(newParent.isRoot)
        return false;
    
    if(newParent.id.search('tree-') == -1)
        return false;

    if(newParent.attributes.has_children){
        Ext.Msg.alert("Ошибка", "Категория имеет подкатегории! Невозможно сопоставить.");
        return false;
    }

    var parent = newParent.id.replace('tree-', '');
    Ext.Ajax.request({
        url: '/category/add_comparison',
        success: function(res) {

            newNode = new Ext.tree.TreeNode({
                text: node.attributes.text,
                draggable: true,
                id: node.id,
                type: 'shop'
            });

            newParent.appendChild(newNode)

            nodesToRemove.push(node.id)
            node.remove();
        },
        params: {target: parent, cur_node: node.id}
    })
})

var yottosTreeRoot = new Ext.tree.AsyncTreeNode({
    text: 'Наше дерево',
    draggable: false,
    id: '0'
});

var yottosTreeLoader = new Ext.tree.TreeLoader({
    dataUrl:'/category/getYottosTreeMatching',
    preloadChildren:true
})

var yottosTree = new Ext.tree.TreePanel({
    root: yottosTreeRoot
    ,autoScroll: true
    ,loader: yottosTreeLoader
    ,dropConfig: {appendOnly:true}
    ,enableDD: true
    ,region:'east'
    ,width:'30%'
    ,useArrows:true
    ,listeners: {
        beforeappend: function(tree, parent, node) {
            var full_pattern = yottosTreeLoader.baseParams.pattern;
            if(full_pattern) {
                var patterns = full_pattern.split(' ');
                for(var patternCounter = 0; patternCounter<patterns.length;patternCounter++) {
                    var pattern = patterns[patternCounter];
                    if (pattern) {
                        var expr = new RegExp('('+pattern+')', 'ig');
                        node.text = node.text.replace(expr, "<span class='highlight'>$1</span>");
                    }
                }
            }
        }
    }
    ,split: true
    ,tbar: new Ext.Toolbar({
        items:[
            {
                text: 'Категории:',
                xtype: 'label'
            },
            '-',
            {
                xtype:'textfield',
                fieldLabel:'Search',
                name: 'pattern',
                id:'category_search_term',
                listeners: {
                    'render': function(c) {
                        c.getEl().on('keypress', function(e) {
                            if(e.getKey() == e.ENTER) {
                                applySearchFilter();
                            }
                        });
                    }
                }
            },
            '->',
            {
                id:'show-done',
                enableToggle: true,
                disabled: true, 
                text:'Показывать сопоставленные',
                handler: function() {
                    if(Ext.getCmp('show-done').pressed){                                        
                        delete yottosTreeLoader.baseParams.pattern;
                        delete goalTreeLoader.baseParams.pattern;
                        Ext.getCmp('category_search_term').setValue('');
                        buildMarketCategories();
                        applySearchFilter();
                    }else{
                        delete yottosTreeLoader.baseParams.pattern;
                        delete goalTreeLoader.baseParams.pattern;
                        Ext.getCmp('category_search_term').setValue('');                        
                        //applySearchFilter();
                    }
                }
            }
        ]
    })
})

yottosTree.on('beforeappend', function(tree, parent, node) {
    if(!node.draggable)
        node.id = 'tree-' + node.id;
});

yottosTree.on('beforeload', function(node) {
    node.id = node.id.replace('tree-', '');
});

yottosTree.on('load', function(node) {
    if(!node.draggable)
        node.id = 'tree-' + node.id;
    marketsGrid.enable();
});


yottosTree.on('beforemovenode', function(tree, node, oldParent, newParent, index) {
    if(newParent.isRoot)
        return false;

    if(newParent.id.search('tree-') == -1)
        return false;

    if(newParent.attributes.has_children){
        Ext.Msg.alert("Ошибка", "Категория имеет подкатегории! Невозможно сопоставить.");
        return false;
    }

    Ext.Ajax.request({
        url: '/category/re_compare',
        success: function(res){
        },
        params: {target: newParent.id.replace('tree-', ''), cur_node: node.id, old: oldParent.id.replace('tree-', '')}
    })
});

var marketsStore = new Ext.data.JsonStore({
    url: '/category/get_Markets',
    root: 'data',
    fields: [
        {
            name: 'id'
        },
        {
            name: 'title'
        },
        {
            name: 'urlMarket'
        }
    ]

})

var marketsGrid = new Ext.grid.GridPanel({
    store: marketsStore,
    colModel: new Ext.grid.ColumnModel({
        defaults: {
            width: 120,
            sortable: true
        },
        columns: [
            {
                header: 'ID',
                width: 30,
                sortable: true,
                dataIndex: 'id'
            },
            {
                id: 'title',
                header: 'Название магазина',
                width: 120,
                sortable: true,
                dataIndex: 'title'
            },
            {
                header: 'URL магазина',
                width: 250,
                sortable: true,
                dataIndex: 'urlMarket',
                renderer: function(value, metaData, record, rowIndex, colIndex, store) {
                    return '<a target="_blank" href="'+value+'">'+value+'</a>';
                }
            }
        ]
    })
    ,listeners: {
        rowclick: function(grid, rowIndex, e) {
            var rec = marketsStore.getAt(rowIndex);
            clearInterval(intervalId);
            marketsGrid.disable();
            market_title = rec.get('title');
            market_id = rec.get('id');
            delete yottosTreeLoader.baseParams.pattern;
            delete goalTreeLoader.baseParams.pattern;
            Ext.getCmp('category_search_term').setValue('');
            buildMarketCategories();
        }
    }
    ,sm: new Ext.grid.RowSelectionModel({singleSelect:true})
    ,frame: false
    ,region:'west'
    ,width:'30%'
    ,split: true,
    title: 'Магазины',
    iconCls: 'icon-grid',
    loadMask: true,
    bbar: new Ext.PagingToolbar({
        pageSize: 20,
        store: marketsStore,
        displayInfo: true,
        displayMsg: 'Показано {0} - {1} из {2}'
    })
});

var nodesToRemove = []

function del_double_from_array(a) {
    a.sort();
    for (var i = a.length - 1; i > 0; i--) {
        if (a[i] == a[i - 1] || a[i] == null) a.splice(i, 1);
    }
}

var intervalId;

function buildMarketCategories() {
    Ext.Ajax.request({
        url: '/category/get_category_from_market',
        params: { market_id: market_id },
        success: function(res) {
            var data = Ext.util.JSON.decode(res.responseText)

            yottosTreeRoot.reload()

            var nodesToRemove = []
            var col = parseInt(data['expand'].length) + 10
            var count = 0

            function nodesExpand() {
                count++
                del_double_from_array(data['nodes'])

                if (count >= col) {
                    clearInterval(intervalId)
                }

                if (data['nodes'].length == 0) {
                    clearInterval(intervalId)
                }

                for (var i = 0; i < data['expand'].length; i++) {
                    try {
                        var node = yottosTree.getNodeById('tree-' + data['expand'][i])

                        node.expand()

                        for (var j = 0; j < data['nodes'].length; j++) {
                            try {
                                if (data['nodes'][j]['pId'] == data['expand'][i]) {
                                    newNode = new Ext.tree.TreeNode({
                                        text: data['nodes'][j]['name'],
                                        draggable: true,
                                        id: data['nodes'][j]['id'],
                                        type: 'shop',
                                        leaf: true
                                    });
                                    node.appendChild(newNode)
                                    nodesToRemove.push(data['nodes'][j]['id'])
                                    data['nodes'].splice(j, 1)
                                }
                            } catch(e) {
                                
                            }
                        }
                    }
                    catch(e) {
                    }
                }

                for (node_counter in data['nodes']) {
                    if (data['nodes'][node_counter].id in nodesToRemove) {
                        delete data['nodes'][node_counter];
                    }
                }

                nodesToRemove = []
            }

            count = 0
            if(Ext.getCmp('show-done').pressed) {
                intervalId = window.setInterval(nodesExpand, 500)
            }
//---------------------------- Market Tree -------------------------
            Ext.getCmp('download-categories-button').disable();
            Ext.getCmp('reset-market').disable();
            Ext.getCmp('show-done').disable();
            
            goalTreeRoot.removeAll();
            goalTreeRoot.reload(function(){
                Ext.getCmp('show-done').enable();
                Ext.getCmp('download-categories-button').enable();
                Ext.getCmp('reset-market').enable();
                goalTreeRoot.enable();
                goalTree.enable();
                if (!goalTreeRoot.childNodes.length) {
                    $.getJSON('/category/getShopTreeStatus', function(response){
                        var message = '';
                        switch(response.status) {
                            case('no_parents'):
                                message = 'Ошибка в струтуре категорий файла выгрузки, не удалось построить дерево';
                                break;
                            case('in_comparison'):
                            message = 'Все категории сопоставлены';
                                break;
                            default:
                            case('no_categories'):
                                message = 'В магазине ещё нет категорий. Загрузите с AdLoad';
                                break;
                        }
                        goalTreeRoot.setText(message)
                    })
                } else {
                    goalTreeRoot.setText(market_title)
                }
            })

            goalTreeRoot.leaf = false;

            goalTreeRoot.expand(false, false);

//---------------------------- End Market Tree ---------------------
        }
    });
}
