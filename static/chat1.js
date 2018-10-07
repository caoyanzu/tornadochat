$(document).ready(function() {          //页面加载完成后调用
	if (!window.console) window.console = {};
	if (!window.console.log) window.console.log = function() {};
	
	//重新定义发送表单'messageform'的submit事件
	$('#messageform').live('submit',function() {
		newMessage($(this));
		return false;
	});
	//定义发送表单'messageform'的keypress事件，使用户在按下回车时也能发送消息
	$('#messageform').live('keypress',function(e) {
		if (e.keyCode == 13) {          //回车键的keyCode为13
			newMessage($(this));
			return false;
		}
	});
	$('#message').select();      //将页面焦点设置在message控件上
	updater.start();
})

function newMessage(form) {
	var message = form.formToDict();   //调用jQuert.fn.formToDict
	updater.socket.send(JSON.stringify(message));  //生成json字符串
	form.find('input[name=body]').val('').select();
}

jQuery.fn.formToDict = function() {    //将表单中所有输入保存到json对象中
	var fields = this.serializeArray();
	var json = {}
	for (var i=0;i<fields.length;i++){
		json[fields[i].name] = fields[i].value;
	}
	if (json.next) delete json.next;
	return json;
};

function add(id,txt) {               //添加元素
	var ul = $('#user_list');   //使用jQuery查找器进行元素定位
	var li = document.createElement('li');  //新建一个li标签
	li.innerHTML = txt;                     //列表项显示字符串
	li.id = id;                             //列表项显示id
	ul.append(li);                //将新建的<li>添加到<ul id='user_list'>中
}

function del(id) {         //删除元素
	$('#'+id).remove();    //找到相应id的元素并删除
}

var updater = {
	socket:null,
	
	start:function() {
		var url = 'ws://' + location.host + '/chatsocket';  //服务器websocket的地址
		updater.socket = new WebSocket(url);          //用WebSocket连接服务器
		
		//定义收到Websocket消息时的行为,即调用showMessage()函数
		updater.socket.onmessage = function(event) {
			updater.showMessage(JSON.parse(event.data));
		}
	},
	showMessage:function(message) {  //将收到的消息显示在页面上
		del(message.client_id);   //在用户面板中删除用户
		if (message.type!='offline'){
			add(message.client_id,message.username);  //在用户面板中添加用户
			if (message.body == '') return;    //如果消息内容为空则返回
			var existing = $('#m' + message.id);
			if (existing.length > 0) return;   //如果消息id已经存在则返回
			var node  = $(message.html);
			node.hide();
			$('#inbox').append(node);    //添加在inbox的底部
			node.slideDown();              //窗口滑到底部
		}
	}
};