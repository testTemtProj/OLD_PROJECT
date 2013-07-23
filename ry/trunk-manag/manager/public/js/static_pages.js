    //TODO вынести в инициализацию
    Ext.MessageBox.buttonText.yes = "Да";
    Ext.MessageBox.buttonText.cancel = "Отмена";
    Ext.MessageBox.buttonText.no = "Нет";

    //TODO Рефакторить, вынести в функции, реализовать без таймаутов
    static_pages_content_tree = new Ext.tree.TreePanel({
            region: 'west',
            id: 'static_pages_content_tree',
            title: 'Структура навигации',
            split: true,
            width: 250,
            minSize: 150,
            autoScroll: true,
            rootVisible: true,
            lines: false,
            useArrows: true,
            collapsible: true,
            baseAttrs: {
                allowChildren: true,
                leaf: false              
            },
            loader: new Ext.tree.TreeLoader({
                dataUrl: '/static/get_pages_tree'
            }),
            root: new Ext.tree.AsyncTreeNode({ id: '0',
                    text: 'Главная',
                    cls: 'folder',
                    draggable: false,
                    leaf: false,
                    expanded: true
                }),
            contextMenu: new Ext.menu.Menu({
                            items: [{
                                    id: 'add-page',
                                    text: 'Добавить',
                                    icon: '/img/add.png'
                                }, {
                                    id: 'delete-page',
                                    text: 'Удалить',
                                    icon: '/img/no.png'
                               }],
                            listeners: {
                                   itemclick: function(item){
                                          var node = item.parentMenu.contextNode;

                                          switch(item.id) {
                                              case 'add-page':
                                                  var unsaved_node = static_pages_content_tree.getNodeById('new-page');
                                                  if (unsaved_node){
                                                      Ext.Msg.alert("Предупреждение", "Не могу добавить страницу. В дереве осталась несохраненная страница.");
                                                      unsaved_node.bubble(function(node){
                                                          node.expand();
                                                      });
                                                      unsaved_node.select();
                                                      edit_static_page(unsaved_node.text, unsaved_node.id);
                                                      return;
                                                  }
                                                  
                                                  if (node.isLeaf()){
                                                      var node_id = node.id;
                                                      node.parentNode.replaceChild({
                                                        id: node.id,
                                                        text: node.text,
                                                        cls: 'folder',
                                                        draggable: false,
                                                        leaf: false
                                                      } , node);
                                                      node = static_pages_content_tree.getNodeById(node_id);
                                                      node.parentNode.expand();
                                                  }
                                                  node.expand();
                                                   
                                                  node.appendChild({
                                                     id: "new-page",
                                                     text: "Новая страница",
                                                     cls: 'folder',
                                                     draggable: false,
                                                     leaf: true 
                                                  });
                                                  //TODO сделать не селектором и убрать таймауты :(
                                                  var new_node = static_pages_content_tree.getNodeById('new-page');
                                                  
                                                  setTimeout(function(){
                                                      new_node.select();
                                                      edit_static_page(new_node.text, new_node.id);
                                                  }, 200);
                                                  break;
                                              case 'delete-page':
                                                  if(node.parentNode){
                                                      var message = 'Вы действительно хотите удалить эту страницу?';
                                                      if (!node.isLeaf()){
                                                          message =  'Вы действительно хотите удалить эту и все вложенные страницы?'; 
                                                      }
                                                      Ext.Msg.show({
                                                          title: 'Удалить?',
                                                          msg: message,
                                                          buttons: Ext.Msg.YESNOCANCEL,
                                                          icon: Ext.MessageBox.QUESTION,
                                                          fn: function(buttonid){
                                                                 switch (buttonid){
                                                                     case 'yes':
                                                                        Ext.Ajax.request({
                                                                            params: {page_id: node.id},
                                                                            url: '/static/remove_page',
                                                                            success: function(result){
                                                                             if (node.isLeaf()){
                                                                                 var node_tab = static_pages_content_tabs.findById(node.id);
                                                                                 if (node_tab){
                                                                                     node_tab.destroy();
                                                                                 }
                                                                             } else {
                                                                               node.eachChild(function(node){
                                                                                     var node_tab = static_pages_content_tabs.findById(node.id);
                                                                                     if (node_tab){
                                                                                         node_tab.destroy();
                                                                                     }
                                                                               });   
                                                                                 var node_tab = static_pages_content_tabs.findById(node.id);
                                                                                 if (node_tab){
                                                                                     node_tab.destroy();
                                                                                 }
                                                                             }
                                                                              var parent_node = node.parentNode;
                                                                              if(parent_node.isRoot){
                                                                                  node.remove();
                                                                                  return;
                                                                              }

                                                                              if (parent_node.childNodes.length == 1){
                                                                                  var parent_node_id = parent_node.id;
                                                                                  parent_node.parentNode.replaceChild({
                                                                                        id: parent_node.id,
                                                                                        text: parent_node.text,
                                                                                        cls: 'folder',
                                                                                        draggable: false,
                                                                                        leaf: true,
                                                                                        expanded:  false 
                                                                                  }, parent_node);
                                                                                  var new_node = static_pages_content_tree.getNodeById(parent_node_id);
                                                                                  new_node.parentNode.expand();
                                                                              } else {
                                                                                  node.remove();
                                                                              }
                                                                            },
                                                                            failure: function(){
                                                                                     Ext.Msg.alert("Ошибка", "Ошибка при сохранении данных");
                                                                            }
                                                                        });
                                                                         break;
                                                                 }
                                                              }
                                                      });
                                                  }
                                                  else {
                                                      Ext.Msg.alert("Предупреждение", "Нельзя удалить корневую страницу");
                                                  }

                                                  break;
                                          }
                                   }
                           }

                 }),
            listeners: {
                    beforedblclick: function(){ return false;},
                    click: function(node, evt){
                           edit_static_page(node.text, node.id);
                       },
                    contextmenu: function(node, e){
                             node.select();
                             var context_menu = node.getOwnerTree().contextMenu;
                             context_menu.contextNode = node;
                             context_menu.showAt(e.getXY());
                       }

           }
        });


    static_pages_content_tabs = new Ext.TabPanel({
            region: 'center',
            defferedRender: false,
            enableTabScroll: true,
            resizeTabs: true,
            defaults: {autoscroll: true},
            minTabWidth: 115,
            tabWidth: 200,
            tbar: new Ext.Toolbar({
                id: 'static-pages-toolbar',
                disabled: true,
                items: [
                    {
                        text: 'Сохранить',
                        listeners: {
                            click: save_static_page
                        }
                    },
                    {
                        text: 'Сбросить',
                        listeners: {
                            click: reset_static_page
                        }
                    },
                    {
                        text: 'Получить ссылкку',
                        listeners: {
                            click: get_page_url
                        }
                    }
                ]
            }),
        });

    function edit_static_page(title, id){
        if (static_pages_content_tabs.find('id', id).length != 0){
            static_pages_content_tabs.setActiveTab(id);
        }
        else { 
            var form_panel = new Ext.form.FormPanel({
                    id: id,
                    title: title,
                    closable: true,
                    layout: 'fit',
                    items: [{
                        xtype: 'fieldset',
                        title: 'Редактирование параметров страницы',
                        collapsible: false,
                        defaultType: 'textfield',
                        defaults: {
                            anchor: '100%'
                        },
                        bodyStyle: 'padding: 5px 25px 0',
                        items: [{
                                fieldLabel: 'Заголовок страницы',
                                name: 'title',
                                allowBlank: false,
                                validator: function(value){
                                    if (value.length > 50){
                                        Ext.Msg.alert('Ошибка валидации', 'Слишком длинный заговок страницы');
                                        return "Слишком длинный заголовок страницы";
                                    }
                                    return true;
                                }
                            }, {
                                fieldLabel: 'Транслит. имя страницы',
                                name: 'slug',
                                allowBlank: false,
                                validator: function(value){
                                    if (value.length > 100){
                                        Ext.Msg.alert('Ошибка валидации', 'Слишком длинный заголовок страницы');
                                        return "Слишком длинное транслитированное имя страницы";
                                    }
                                    return true;
                                }
                            }, {
                                fieldLabel: 'Текст',
                                xtype: 'textarea',
                                cls: 'mceEditor',
                                name: 'content'
                        }]
                    }],
                    listeners: {
                           close: function(tab){
                              if(tab.id == 'new-page'){
                                  var new_node = static_pages_content_tree.getNodeById('new-page');
                                  if (new_node == null){
                                      return;
                                  }
                                  var parent_node = new_node.parentNode;
                                  if (parent_node.isRoot){
                                      new_node.remove();
                                      return;
                                  }
                                  if (parent_node.childNodes.length == 1){
                                      var parent_node_id = parent_node.id;
                                      parent_node.parentNode.replaceChild({
                                            id: parent_node.id,
                                            text: parent_node.text,
                                            cls: 'folder',
                                            draggable: false,
                                            leaf: true,
                                            expanded:  false 
                                      }, parent_node);
                                      var new_node = static_pages_content_tree.getNodeById(parent_node_id);
                                      new_node.parentNode.expand();
                                  } else {
                                      new_node.remove();
                                  }

                              }
                              if(static_pages_content_tabs.items.length == 1)
                                  Ext.getCmp('static-pages-toolbar').disable();
                           }
                    }

                });

            if (id != 'new-page') {
                form_panel.getForm().load({
                    url: '/static/get_page',
                    params: {
                        page_id: id
                        },
                    failure: function() {
                                 Ext.Msg.alert("Ошибка", "Ошибка при загрузке данных");
                             }
                });
            }
            static_pages_content_tabs.add(form_panel);
            static_pages_content_tabs.setActiveTab(id);
            var static_pages_toolbar = Ext.getCmp('static-pages-toolbar');
            if(static_pages_toolbar.disabled)
                static_pages_toolbar.enable();
            setTimeout(setup, 1000);
        }
    }

    
    function reset_static_page(){
        var active_tab = static_pages_content_tabs.getActiveTab();
        var id = active_tab.id
        active_tab.getForm().load({
            url: '/static/get_page',
            params: {
                page_id: id
                },
            failure: function() {
                         Ext.Msg.alert("Ошибка", "Ошибка при загрузке данных");
                     }
        });

        //если есть tinyMCE - извращаемся, сука через iframe работает
        if (tinyMCE){
            try{
                var content_area = active_tab.findByType('textarea')[0];
            } catch(e){
                console.log(e);
                return;
            }
            var value = content_area.getRawValue();
            if (value)
                tinyMCE.get(content_area.id).setContent(value);
            setTimeout(setup, 1000);
        }
    }


    function save_static_page(){
        var active_tab = static_pages_content_tabs.getActiveTab();
        var page_id = active_tab.id;
        var form = active_tab.getForm();
        var values = form.getValues();

        if (tinyMCE){
            try{
                var content_area = active_tab.findByType('textarea')[0];
            } catch(e){
                console.log(e);
                return;
            }

            var content = tinyMCE.get(content_area.id).getContent();
            values['content'] = content;
        }

        values['page_id'] = page_id;

        var tree_node = static_pages_content_tree.getNodeById(page_id);
        tree_node.setText(values['title']);
        values['parent_id'] = tree_node.parentNode.id;

        Ext.Ajax.request({
            params: values,
            url: '/static/save_page',
            success: function(result){
                var page_id = Ext.decode(result.responseText).page_id;
                if(page_id == false){
                    return Ext.Msg.alert('Ошибка', "Не могу сохранить. Такое транслитированное имя есть у другой страницы.");
                }

                if (values['page_id'] == 'new-page'){
                    tree_node.setId(page_id);
                }
                active_tab.destroy();
            },
            failure: function(){
                     Ext.Msg.alert("Ошибка", "Ошибка при сохранении данных");
            }
        });
    }

    function get_page_url(){
        var slug = static_pages_content_tabs.getActiveTab().getForm().getValues()['slug'];
        var startCharacters = "/";
        var endCharacters = ".html";
        var uri = '';

        slug = slug.replace(/&nbsp;/g," ");
        slug = slug.replace(/(^\s+)|(\s+$)/g, "");

        if(slug){
            if(slug.substring(0, 1) == '/')
                startCharacters = '';

            if (slug.length >= 5)
                if(slug.substring(slug.length - 4) == ".html")
                    endCharacters = '';

            uri = startCharacters + slug + endCharacters;

            Ext.Msg.alert("Ссылка на страницу", uri);
        }
        else
            Ext.Msg.alert("Ошибка", "Транслитированное имя не заполнено.");
    }
