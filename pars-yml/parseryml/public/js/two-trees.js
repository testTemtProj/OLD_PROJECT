
var nodesToRemove = []
function del_doble_from_array(a)
{
	a.sort();
	for (var i = a.length - 1; i > 0; i--) {
		if (a[i] == a[i - 1]) a.splice( i, 1);
	}
}

Ext.EventManager.onDocumentReady(function(){
	//------------------------------ Yottos Tree -----------------------
	
	var yottosTreeRoot = new Ext.tree.AsyncTreeNode({
		text: 'Наше дерево', 
		draggable:false, 
		id:'0'
	});
	
	var yottosTree = new Ext.tree.TreePanel({
		root: yottosTreeRoot,
		autoScroll:true,
		loader: new Ext.tree.TreeLoader({dataUrl:'/category/getYottosTreeMatching'}),
		dropConfig: {appendOnly:true},
		enableDD: true,
	})
	
	yottosTree.render('tree')
	
	yottosTreeRoot.expand(false, false);
	
	yottosTree.on('beforemovenode', function(tree, node, oldParent, newParent, index){
		Ext.Ajax.request({
			url: '/category/re_compare',
			success: function(res){
				
			},
			params: {target: newParent.id, cur_node: node.id, old: oldParent.id}
		})
	})
	
	//---------------------------- End Yottos Tree ---------------------
		
	//---------------------------- Market Grid -------------------------
	
	var marketsStore = new Ext.data.JsonStore({
		url: '/category/get_Markets',
		root: 'data',
		fields: [
			{
				name: 'id'
			},{
				name: 'title'
			}, {
				name: 'urlMarket'
			}
		]
	
	});
	
	marketsStore.load()
	
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
				},{
					id: 'title',
					header: 'Название магазина', 
					width: 120,
					sortable: true, 
					dataIndex: 'title'
				},{
					header: 'URL магазина',
					width: 250, 
					sortable: true,  
					dataIndex: 'urlMarket',
				},{
                xtype: 'actioncolumn',
                id: 'date',
                width: 50,
                items: [{
						icon   : '/img/up.png',
						handler: function(grid, rowIndex, colIndex) {
							
							var rec = marketsStore.getAt(rowIndex)
							id = rec.get('id')
							
							document.getElementById('tree2').innerHTML = ''
							
							Ext.Ajax.request({
								url: '/category/get_category_from_market',
								success: function(res){
									
									data = eval( "(" + res.responseText + ")" )
									var s = true
									del_doble_from_array(data['expand'])
									
									yottosTreeRoot.eachChild(function(){
										this.collapse()
									})
									
									function nodesExpand()
									{
										del_doble_from_array(nodesToRemove)
										for(var i=0; i<nodesToRemove.length; i++)
										{
											try
											{
												var node = yottosTree.getNodeById(nodesToRemove[i])
												node.remove()
											}
											catch(e){console.log(nodesToRemove[i])}
										}
										nodesToRemove = []
										
										for(var i=0; i<data['expand'].length; i++)
										{
											try
											{
												var node = yottosTree.getNodeById(data['expand'][i])
												
												node.expand()
												for(var j=0; j<data['nodes'].length; j++)
												{
													if(data['nodes'][j]['pId'] == data['expand'][i])
													{
														newNode = new Ext.tree.TreeNode({
															text: data['nodes'][j]['name'], 
															draggable: true,
															icon: '/js/ext/resources/images/default/tree/_leaf.gif',
															id:data['nodes'][j]['id'],
															type: 'shop'
														});					
														node.appendChild(newNode)
														nodesToRemove.push(data['nodes'][j]['id'])
													}
													
												}
												s = true
											}
											catch(e){s = false;}
										}
										if(s == true)
										{
											clearInterval(intervalId)
										}
									}
									intervalId = window.setInterval(nodesExpand, 500)
									
	//---------------------------- Market Tree -------------------------
	
									var marketTreeRoot = new Ext.tree.AsyncTreeNode({
										text: 'Дерево магазина', 
										draggable: true,
										id:'0'
									});
									
									var marketTree = new Ext.tree.TreePanel({
										root: marketTreeRoot,
										autoScroll:true,
										enableDD: true,
										loader: new Ext.tree.TreeLoader({dataUrl:'/category/getShopTree'}),
										dropConfig: {appendOnly:true},
									})
									
									marketTree.render('tree2')
									
									marketTreeRoot.expand(false, false);
									
									marketTree.on('beforemovenode', function(tree, node, oldParent, newParent, index) {
										Ext.Ajax.request({
											url: '/category/add_comparison',
											success: function(res){
												nodesToRemove.push(node.id)
											},
											params: {target: newParent.id, cur_node: node.id}
										})
									})
	
	//---------------------------- End Market Tree ---------------------
								},
								params: { market_id: id }
							});
						}
					}]
				}],
		}),
		sm: new Ext.grid.RowSelectionModel({singleSelect:true}),
		height: 660,
		frame: true,
		title: 'Магазины',
		iconCls: 'icon-grid',
		loadMask: true,
		clicksToEdit:'1',
		bbar: new Ext.PagingToolbar({
            pageSize: 20,
            store: marketsStore,
            displayInfo: true,
            displayMsg: 'Показано {0} - {1} из {2}',
        })
	});
	
	marketsGrid.render('markets');
	
	//---------------------------- End Market Grid ---------------------
	
	//---------------------------- Tool-Tip ----------------------------
	new Ext.ToolTip({        
		title: 'Нужна Помощь?',
		id: 'content-anchor-tip',
		target: 'compareHelp',
		anchor: 'left',
		html: null,
		width: 200,
		autoHide: false,
		closable: true,
		contentEl: 'tip', // load content from the page
		listeners: {
			'render': function(){
				this.header.on('click', function(e){
					e.stopEvent();
					Ext.Msg.alert('Link', 'Link to something interesting.');
					Ext.getCmp('content-anchor-tip').hide();
				}, this, {delegate:'a'});
			}
		}
	});
});
