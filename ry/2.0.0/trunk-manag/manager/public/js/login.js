Ext.EventManager.onDocumentReady(function(){
	login_field = new Ext.form.TextField({
		fieldLabel: 'Login',
		name: 'login',
		anchor:'100%',
		listeners: {
			specialkey: function(f,e)
			{
				if (e.getKey() == e.ENTER) 
				{
					login_window.getEl().mask('Login...');
                       
					Ext.Ajax.request({
						url: '/campaigns/login',
						params: {user_login: login_form.getForm().getValues().login,
								 user_password: login_form.getForm().getValues().password},
						success: function (result, request) {                                                           
							if (result.responseText != '') {
								Ext.MessageBox.show({
									title: 'Error',
									msg: 'Не верный логин либо пароль',
									minWidth: 200,
									bottons: Ext.MessageBox.OK,
									icon: Ext.MessageBox.WARNING
								});
								login_window.getEl().unmask(true);                                   
							} else {
								window.location.href = '/';
								window.event.returnValue = false;
							}
						},
						failure: function ( result, request ) {
							Ext.MessageBox.show({
								title: 'Error',
								msg: '500 Server Error',
								minWidth: 200,
								bottons: Ext.MessageBox.OK,
								icon: Ext.MessageBox.WARNING
							});
							login_window.getEl().unmask(true);
						}
					});
				}
			}
		}
	})
	
	password_field = new Ext.form.TextField({
		fieldLabel: 'Password',
		name: 'password',
		inputType: 'password',
		anchor: '100%',
		listeners: {
			specialkey: function(f,e)
			{
				if (e.getKey() == e.ENTER) 
				{
					login_window.getEl().mask('Login...');
                       
					Ext.Ajax.request({
						url: '/campaigns/login',
						params: {user_login: login_form.getForm().getValues().login,
								 user_password: login_form.getForm().getValues().password},
						success: function (result, request) {                                                           
							if (result.responseText != '') {
								Ext.MessageBox.show({
									title: 'Error',
									msg: 'Не верный логин либо пароль',
									minWidth: 200,
									bottons: Ext.MessageBox.OK,
									icon: Ext.MessageBox.WARNING
								});
								login_window.getEl().unmask(true);                                   
							} else {
								window.location.href = '/';
								window.event.returnValue = false;
							}
						},
						failure: function ( result, request ) {
							Ext.MessageBox.show({
								title: 'Error',
								msg: '500 Server Error',
								minWidth: 200,
								bottons: Ext.MessageBox.OK,
								icon: Ext.MessageBox.WARNING
							});
							login_window.getEl().unmask(true);
						}
					});
				}
			}
		}
	})
	
	login_form = new Ext.form.FormPanel({
		labelWidth: 55,
		frame: true,
		defaultType: 'textfield',
		items: [login_field,password_field],
	});
	
	login_window = new Ext.Window({
        title: '',
        width: 300,
        height: 150,
        layout: 'fit',
        plain:true,
        closable: false,
        bodyStyle:'padding:5px;',
        items: login_form,
        buttons: [{ text: 'Login', handler :
                    function() {
                        login_window.getEl().mask('Login...');
                       
                        Ext.Ajax.request({
                            url: '/campaigns/login',
                            params: {user_login: login_form.getForm().getValues().login,
                                     user_password: login_form.getForm().getValues().password},
                            success: function (result, request) {                                                           
                                if (result.responseText != '') {
                                    Ext.MessageBox.show({
                                        title: 'Error',
                                        msg: 'Не верный логин либо пароль',
                                        minWidth: 200,
                                        bottons: Ext.MessageBox.OK,
                                        icon: Ext.MessageBox.WARNING
                                    });
                                    login_window.getEl().unmask(true);                                   
                                } else {
                                    window.location.href = '/';
                                    window.event.returnValue = false;
                                }
                            },
                            failure: function ( result, request ) {
								Ext.MessageBox.show({
									title: 'Error',
									msg: '500 Server Error',
									minWidth: 200,
									bottons: Ext.MessageBox.OK,
									icon: Ext.MessageBox.WARNING
								});
								login_window.getEl().unmask(true);
							}
                        });
                    }
                 }]
    });
	
	login_window.show()
});
