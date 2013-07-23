/** Присваивает каждому пользователю поле lastPaymentType -- тип вывода средств,
 * 	который использовался в последний раз.
 */
db.users.find().forEach(function(user) {
	var req = db.money_out_request.find({'user.login': user.login}).sort({date: -1})[0];
	if (!req)
		return;
	user.lastPaymentType = req.paymentType;
	db.users.save(user);
})
