var Tree = Ext.tree;

Ext.EventManager.onDocumentReady(function(){
	tree = new Tree.TreePanel({
		animate:true, 
		autoScroll:true,
		//useArrows: true,
		loader: new Ext.tree.TreeLoader({dataUrl:'/category/getYottosTreeSettings'}),
		enableDD:true,
		containerScroll: true,
		border: false,
		rootVisible: false,
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
						root.eachChild(function(){
							this.expand()
						})
					}
					else
					{
						root.eachChild(function(){
							this.collapse()
						})
					}
				}
			}]
        })
	});
	
	new Tree.TreeSorter(tree, {folderSort:true});
	
	var root = new Tree.AsyncTreeNode({
		text: 'Наше дерево', 
		draggable:false, 
		id:'0'
	});
	tree.setRootNode(root);
	
	tree.render('settingtree');
	
	root.expand(false, false);
	
	var contextMenu = new Ext.menu.Menu({
	items: [
		{ text: 'Добавить', handler: addHandler },
		{ text: 'Редактировать', handler: changeHandler },
		{ text: 'Переименовать', handler: renameHandler },
		{ text: 'Удалить', handler: deleteHandler }]
	})
	
	tree.on('contextmenu', treeContextHandler);
	
	var curNode;
	form = new Ext.FormPanel({
        labelWidth: 100, // label settings here cascade unless overridden
        url:'save-form.php',
        frame:false,
        bodyStyle:'padding:5px 5px 0',
        defaultType: 'textfield',
		labelAlign: 'left',
        items: [{
				fieldLabel: 'Имя категории',
				name: 'Name',
				anchor:'100%'
			},{
				fieldLabel: 'Title',
				name: 'Title',
				anchor:'100%'
			},{
				fieldLabel: 'Meta Key',
				name: 'MetaKey',
				anchor:'100%'
			},{
				fieldLabel: 'Описание',
				name: 'Description',
				xtype: 'textarea',
				anchor:'100%'
			}],
    });
    form2 = new Ext.FormPanel({
        labelWidth: 100, // label settings here cascade unless overridden
        url:'save-form.php',
        frame:false,
        bodyStyle:'padding:5px 5px 0',
        defaultType: 'textfield',
		labelAlign: 'left',
        items: [{
				fieldLabel: 'Имя категории',
				name: 'Name',
				anchor:'100%'
			},{
				fieldLabel: 'Title',
				name: 'Title',
				anchor:'100%'
			},{
				fieldLabel: 'Meta Key',
				name: 'MetaKey',
				anchor:'100%'
			},{
				fieldLabel: 'Описание',
				name: 'Description',
				xtype: 'textarea',
				anchor:'100%'
			}],
    });
    win = new Ext.Window({
		layout:'fit',
		width:500,
		height:217,
		closeAction:'hide',
		plain: true,
		items: [form2],
		buttons: [{
			text:'Сохранить',
			handler: function(){
				items = form2.items.items
				var data = {}
				data['ParentID'] = curNode.id
				for(var i = 0; i < items.length; i++)
				{
					data[items[i].getName()] = items[i].getValue();
				}
				Ext.Ajax.request({
					url: '/category/add',
					success: function(res){
						obg = Ext.util.JSON.decode(res.responseText)
						newNode = new Ext.tree.TreeNode({
							text: data['Name'],
							cls: 'folder',
							id: obg
						})
						curNode.appendChild(newNode)
						items = form2.items.items
						for(var i = 0; i < items.length; i++)
						{
							items[i].setValue('')
						}
						win.hide();
					},
					params: { cat: JSON.stringify(data) }
				});
			}
		},{
			text: 'Отменить',
			handler: function(){
				win.hide();
			}
		}]
	});
	
	win2 = new Ext.Window({
		layout:'fit',
		width:500,
		height:217,
		closeAction:'hide',
		plain: true,
		items: [form],
		buttons: [{
			text:'Сохранить',
			handler: function(){
				items = form.items.items
				var data = {}
				data['ID'] = curNode.id
				for(var i = 0; i < items.length; i++)
				{
					data[items[i].getName()] = items[i].getValue();
				}
				Ext.Ajax.request({
					url: '/category/change',
					success: function(res){
						obg = Ext.util.JSON.decode(res.responseText)
						newNode = new Ext.tree.TreeNode({
							text: data['Name'],
							cls: 'folder',
							id: obg
						})
						curNode.appendChild(newNode)
						items = form.items.items
						curNode.setText(items[0].getValue())
						for(var i = 0; i < items.length; i++)
						{
							items[i].setValue('')
						}
						win2.hide();
					},
					params: { cat: JSON.stringify(data) }
				});
			}
		},{
			text: 'Отменить',
			handler: function(){
				win2.hide();
			}
		}]
	});
	
	function changeHandler()
	{
		Ext.Ajax.request({
			url: '/category/get_category',
			success: function(res){
				obg = Ext.util.JSON.decode(res.responseText)
				item = form.items.items
				item[0].setValue(obg['Name'])
				item[1].setValue(obg['Title'])
				item[2].setValue(obg['MetaKey'])
				item[3].setValue(obg['Description'])
				win2.show()
			},
			params: { id: curNode.id }
		});
	}
	
	function addHandler(){
		win.show(this);
		win.on('hide', function(){
			items = form.items.items
			for(var i = 0; i < items.length; i++)
			{
				items[i].setValue('')
			}	
		});    
	}
	function treeContextHandler(node) {
		node.select();
		curNode = node;
		contextMenu.show(node.ui.getAnchor());
	}
	var deleting = function(btn){
		if(btn == 'yes')
		{
			Ext.Ajax.request({
				url: '/category/remove',
				success: function(data){
					tree.getSelectionModel().getSelectedNode().remove();
				},
				params: { catId: curNode.id }
			});
		}
	};
	function deleteHandler() {
		var ms = 'Вы действительно хотите удалить категорию -<h2><b>'+curNode.text+'?</b></h2>'
		Ext.Ajax.request({
			url: '/category/getYottosTreeSettings',
			success: function(data){
				obg = Ext.util.JSON.decode(data.responseText);
				if(obg.length != 0)
				{
					ms+= 'С подкатегориями:'
				}
				for(var i=0;i<obg.length;i++)
				{
					ms += "<h1>"+obg[i]['text']+"</h1>"
				}
				Ext.MessageBox.show({
					title:'Удалить?',
					msg: ms,
					buttons: Ext.MessageBox.YESNO,
					fn: deleting,
					icon: Ext.MessageBox.QUESTION,
					height: 200,
					width: 350
				});
			},
			params: { node: curNode.id }
		});
	}
	var editor = new Ext.tree.TreeEditor(tree);
	editor.on('beforecomplete', function(editor, newValue, originalValue)
	{
		Ext.Ajax.request({
			url: '/category/rename',
			success: function(data){
				
			},
			params: { catId: this.editNode.id, newName: newValue}
		});
	});
	function renameHandler(){
		editor.triggerEdit(curNode);
	}
	
	//Tool Tip
	
	new Ext.ToolTip({        
		title: 'Нужна Помощь?',
		id: 'content-anchor-tip',
		target: 'leftCallout',
		anchor: 'left',
		html: null,
		width: 200,
		autoHide: false,
		closable: true,
		contentEl: 'content-tip', // load content from the page
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
