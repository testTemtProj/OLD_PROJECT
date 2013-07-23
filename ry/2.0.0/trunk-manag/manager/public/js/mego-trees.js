function initTree() {
	var tree = Ext.getCmp('rynok-tree')
	
	var sorter = new Ext.tree.TreeSorter(tree, {folderSort:false});

    var root = tree.root;
	root.expand(false, false);
	
	var contextMenu = new Ext.menu.Menu({
	items: [
		{ text: 'Добавить', handler: addHandler, icon: '/img/add.png' },
		{ text: 'Редактировать', handler: changeHandler, icon: '/img/edit.png' },
	//	{ text: 'Переименовать', handler: renameHandler, icon: '/img/rename.png' },
		{ text: 'Удалить', handler: deleteHandler, icon: '/img/no.png' }]
	})

    var rootContextMenu = new Ext.menu.Menu({
	    items: [{
            text: 'Добавить',
            handler: addHandler,
            icon: '/img/add.png'
        }]
	})
	

	var oldPosition = null;
    var oldNextSibling = null;

    tree.on('contextmenu', treeContextHandler);
    
    tree.on('startdrag', function(tree, node, event){
        oldPosition = node.parentNode.indexOf(node);
        oldNextSibling = node.nextSibling;
    });

    tree.on('movenode', function(tree, node, oldParent, newParent, position){

        if (oldParent != newParent){
            var url = '/category/reparent';
            var params = {'node':node.id, 'parent':newParent.id, 'position':position};
        }

        tree.disable();

        Ext.Ajax.request({
            url:url,
            params:params,
            success:function(response, request) {

                if (response.responseText.charAt(0) != 1){
                    request.failure();
                } else {
                    tree.enable();
                }
            },
            failure:function() {
                tree.suspendEvents();
                oldParent.appendChild(node);
                if (oldNextSibling){
                    oldParent.insertBefore(node, oldNextSibling);
                }
                tree.resumeEvents();
                tree.enable();
                console.log("Oh no! Your changes could not be saved!");
            }

        });

    });

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
				fieldLabel: 'Альтернативное имя (не больше 15 символов)',
				name: 'AlternativeTitle',
				anchor:'100%',
                validator: function(value){
                    if(value.length > 15){
                        return "Длина имени больше 15 символов.";
                    }
                    return true;
                }
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
			},{
				fieldLabel: 'Баннер',
				name: 'Baner',
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
				id: 'category-title',
                fieldLabel: 'Имя категории',
				name: 'Name',
				anchor:'100%'
			},{
				fieldLabel: 'Альтернативное имя (не больше 15 символов)',
				name: 'AlternativeTitle',
				anchor:'100%',
                validator: function(value){
                    if(value.length > 15){
                        return "Длина имени больше 15 символов.";
                    }
                    return true;
                }
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
			},{
				fieldLabel: 'Баннер',
				name: 'Baner',
				xtype: 'textarea',
				anchor:'100%'
			}],
    });
    win = new Ext.Window({
        title:'Создание новой категории',
        modal: true,
		layout:'fit',
		width:500,
		height:354,
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
							text: obg.Name,
							cls: 'folder',
							id: obg.ID,
                            leaf: false
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
		height:354,
        modal: true,
		closeAction:'hide',
		plain: true,
        title: 'Редактировать категорию',
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
                            leaf: false,
							id: obg
						})
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
                item[1].setValue(obg['AlternativeTitle'])
				item[2].setValue(obg['Title'])
				item[3].setValue(obg['MetaKey'])
				item[4].setValue(obg['Description'])
				item[5].setValue(obg['banner'])
				win2.show()
			},
			params: { id: curNode.id }
		});
	}
	
	function addHandler(){
		win.show();
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
        if(curNode.id>0)
		    contextMenu.show(node.ui.getAnchor());
        else
            rootContextMenu.show(node.ui.getAnchor());
	}
	var deleting = function(btn){
		if(btn == 'yes')
		{
            var selectedNode = tree.getSelectionModel().getSelectedNode();
            selectedNode.remove();

			Ext.Ajax.request({
				url: '/category/remove',
				success: function(data){

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
};
