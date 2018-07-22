# encoding: utf-8

from PyQt5.QtCore import QObject, QUrl
from PyQt5.Qt import QQmlApplicationEngine
from PyQt5.QtWidgets import QApplication


from twisted.internet.protocol import Protocol, ClientFactory
import json

#from twisted.internet import reactor
#from threading import Thread
global _TradePorto
global g_RequestID
g_RequestID = 0
btnConnectTrade = QObject
btnConnectCommand = QObject
textEndpoint = QObject
textAreaReplyMsg = QObject
textAreaReplyData = QObject
textAreaSend = QObject
btnCurrentPage = QObject
def drop_connect() :
    _TradePorto.transport.abortConnection()

class TSClntProtocol(Protocol):
    m_nResCount = 0
    m_mapPage2Res = {}
    def dataReceived(self, recv_data):
        recv_data = recv_data.decode("UTF-8")
        #定义一个是否接受数据的标识
        recv_length = len(recv_data)
        while 1:
            (resume_data_size, single_package) = self.package_retriver(recv_data, recv_length)

            if resume_data_size == -2 :
                #未完成继续接收
                return
            elif resume_data_size == -1 :
                #解析发生错误,关闭连接
                print ('解析发生错误,关闭连接')
                self.transport.abortConnection()
                
            #do rpc action here
            #d = threads.deferToThread(functools.partial(self.package_demultiplex, tcp_package))
            #d.addCallback(self.send_response)
            #d.addErrback(self.send_response)
            res_data = ''
            jsonObjReply = json.loads(single_package)
            #print(json.dumps(json.loads(jsonObjReply['data']), indent=4, sort_keys=False))
            if jsonObjReply['data'][:1] == '{' :
                #parsed = json.loads(jsonObjReply['data'])
                #text2show = json.dumps(parsed, indent=4, sort_keys=False)
                #text2show = text2show.replace('\n', '<br>')
                #text2show = text2show.replace(' ', '&nbsp;')
                res_data = json.dumps(json.loads(jsonObjReply['data']), indent=4, sort_keys=False).replace('\n', '<br>').replace(' ', '&nbsp;')#text2show
            elif jsonObjReply['data'][:1] == ',' :#判断为原始数据
                res_data = '<table border="1"><tr>' + jsonObjReply['data'].replace(',','<td>').replace('\n','<tr>') + '</tr></table>'
            
            textAreaReplyData.setProperty('text', res_data)

            res_msg = ''
            if jsonObjReply['success'] == False :
            #This is some text!</font>'
                res_msg = 'id:' + jsonObjReply["id"] + '<br>' +'msg:' + jsonObjReply["msg"] + '<br>' + '<font size="5" color="red"><b>' + 'success:' + ('true' if jsonObjReply["success"] else 'false') + '</b></font>'
            else :
                res_msg = 'id:' + jsonObjReply["id"] + '<br>' +'msg:' + jsonObjReply["msg"] + '<br>' + '<font size="5" color="green"><b>' + 'success:' + ('true' if jsonObjReply["success"] else 'false') + '</b></font>'
            textAreaReplyMsg.setProperty('text', res_msg)
            #self.m_nResCount = self.m_nResCount + 1
            #global g_nResCount
            #g_nResCount += 1
            self.m_nResCount += 1
            main.m_nCurrentPage = self.m_nResCount
            btnCurrentPage.setProperty('text', '- ' + str(self.m_nResCount) + ' -')
            self.m_mapPage2Res[self.m_nResCount] = (textAreaSend.property('text'), res_data, res_msg)
            #print('Curr Res Count:%d,Curr Page:%d'%(self.m_nResCount,main.m_nCurrentPage))

            #'id': '1', 'msg': '当前未处于交易时间', 'success': False}
            # self.send_response(tcp_package.encode('utf-8'));
            
            #缓存已解析完毕
            if resume_data_size == 0 :
                break
            
            #print "Enter Unexcepted Handler"
            recv_data = ''
            recv_length = 0
       
    def send_data(self, data):
        # data = input('> ')
        if data:
            print('发送数据包:%s' % data)
            self.transport.write(data.encode("UTF-8") + b'\n')
        #else:
        #    self.transport.loseConnection()
    def echo(self, data) :
        self.transport.write(data)
        
    m_DataBuffer = ""
    def package_retriver(self, recv_data, recv_length):
        bHasCachce = False
        package = ""
        parse_buffer = ""
        if len(self.m_DataBuffer) == 0 or self.m_DataBuffer == "" :
            if recv_length == 0 or recv_data == "" :
                return -2,''
            parse_buffer = recv_data
        else:
            bHasCachce = True
            if recv_data != '' and recv_length != 0 :  
                self.m_DataBuffer += recv_data
            parse_buffer = self.m_DataBuffer        


        #判断解析的数据类型
        if not '{' == parse_buffer[0] : #not parse_buffer.startswith('{') :
            if bHasCachce == True:
                self.m_DataBuffer = ""
            return -1,''

        #判断数据结尾
        bFindEnd = False
        index_cursor = 0
        for chIter in parse_buffer:
            if '\n' == parse_buffer[index_cursor] :
                bFindEnd = True
                break
            index_cursor += 1
        
        #未完成 放入缓存下次数据达到继续解析
        if bFindEnd == False : 
            if bHasCachce == False :
                self.m_DataBuffer += recv_data
            return -2,''
        
        	#完成后整理出数据包
        package = parse_buffer[:index_cursor+1]

			#整理缓存
        if bHasCachce == True : 
            self.m_DataBuffer = self.m_DataBuffer[index_cursor + 1 : ]
        else :
            if (index_cursor + 1) < recv_length :
                self.m_DataBuffer += recv_data[ index_cursor + 1 :  recv_length - index_cursor - 1]
        return len(self.m_DataBuffer), package

    """
    def reply_package_demultiplex(self, single_package) : 
        try : 
            json_object = json.loads(single_package)
            action = json_object['action']
            print ('Current action : %s' % action)
        except : 
            print ("转换成json数据失败:%s" % single_package)
            return "Error Packaget"
        return action
    """    

#currProto = TSClntProtocol

class TSClntFactory(ClientFactory):
    protocol = TSClntProtocol
    #clientConnectionLost = clientConnectionFailed = lambda self, connector, reason: reactor.stop()
    
    def startedConnecting(self, connector):
        print('Started to connect.')
    
    def buildProtocol(self, addr):
        print('Connected.')
        btnConnectTrade.setProperty('text', '已连接')  
        global _TradePorto
        _TradePorto = TSClntProtocol()
        #print(currProto, currProto.connected, currProto.transport)
        #currProto.factory = self
        return _TradePorto
        #return TSClntProtocol()
    
    def clientConnectionLost(self, connector, reason):
        print('Lost connection. Reason:', reason)
        btnConnectTrade.setProperty('text', '未连接')
        reactor.stop()
     
    def clientConnectionFailed(self, connector, reason):
        print('Connection failed. Reason:', reason)
        reactor.stop()
        #原因
        

    
if __name__=='__main__':
    import sys

class Main(QObject):
    m_nCurrentPage = 0
    def on_click(self, btnName, strContent):
        if btnName == "连接交易" : 
            if(btnConnectTrade.property('text') == '未连接') :
                nSplitPos = strContent.find(':')
                if nSplitPos <= 0 :
                    return
                Host = strContent[:nSplitPos]
                Port = int(strContent[nSplitPos + 1 :])
                print("connecting host %s:%d" %(Host, Port))
                reactor.connectTCP(Host, Port, TSClntFactory())
                if not reactor.running:
                    reactor.run();
            else:
                print('中断连接')
                if reactor.running:
                    reactor.stop()
                drop_connect()

        elif btnName == "连接命令" :
            print("连接命令")
            print(main.window.findChild(QObject, "res_msg"))
            #btnConnectCommand.setProperty('text', '正在连接')
            #_TradePorto.send_data(b'HEHE')
        elif btnName == "发送" :
            #print(strContent)
            reactor.callLater(0, _TradePorto.send_data(strContent.replace('\n','').replace('\t','')))
        elif btnName == '生成' :
            strRequestData=''
            json_object = json.loads(strContent)
            action = (json_object["操作"])
            if action == 'PlaceOrder' :
                #c = json_object["股票代码"]
                #print("股票:%s"%c)
                #print(json_object["交易市场"])
                jsonObj_order = {
                    "c": json_object["股票代码"],
                    "f": 0 if (json_object["交易市场"] == '做多') else 1,
                    "g": 0,
                    "info": "ip=,lip=,mac=,hd=,cpu=,pcn=",
                    "ip": json_object["IP"],
                    "m": 0 if (json_object["交易市场"] == '上海') else 1,
                    "mac": "",
                    "n": "",
                    "okey": "",
                    "ownedbygltrade": 0,
                    "p": float(json_object["送单价格"]),
                    "q": int(json_object["送单数量"]),
                    "rid": 0,
                    "t": 5,
                    "uefK": "",
                    "x": 0
                }
                strRequestData=json.dumps(jsonObj_order)
            elif (action == 'CancelOrder' or action == 'GetEntrust' or action == 'GetInTimeEntrust'):
                jsonObj_order = {
                    "c": json_object["股票代码"],
                    "f": 0 if (json_object["交易市场"] == '做多') else 1,
                    "g": 0,
                    "info": "ip=,lip=,mac=,hd=,cpu=,pcn=",
                    "ip": json_object["IP"],
                    "m": 0 if (json_object["交易市场"] == '上海') else 1,
                    "mac": "",
                    "n": json_object['委托单号'],
                    "okey": "",
                    "ownedbygltrade": 0,
                    "p": float(json_object["送单价格"]),
                    "q": int(json_object["送单数量"]),
                    "rid": 0,
                    "t": 5,
                    "uefK": "",
                    "x": 0
                }
                strRequestData=json.dumps(jsonObj_order)
            elif(action == 'GetResourceData'):
                d = {"资金":0,"持仓":1,"当日委托":2,"当日成交":3,"可撤单":4,"股东代码":5,"普通交易":6,"融资余额":7,"融券余额":8,"可融证券":9,"历史委托":10,"历史成交":11,"资金流水":12,"交割单":13,"融资负债":14}                       
                jsonQryResource = {
                 "end": json_object['开始时间'],
                	"rid": 0,
                	"start": json_object['结束时间'],
                	"type": d[json_object['原始数据']]
                }
                strRequestData=json.dumps(jsonQryResource)

                   
            global g_RequestID
            g_RequestID += 1
            jsonbj_request = {
            	"action": action,
            	"bi": textEndpoint.property('text'),
            	"data": strRequestData,
            	"id": str(g_RequestID)
            }
            textAreaSend.setProperty('text', json.dumps(jsonbj_request))
            
        elif(btnName == '清空'):
            textAreaSend.setProperty('text', '')
            textAreaReplyMsg.setProperty('text', '')
            textAreaReplyData.setProperty('text', '')
        elif(btnName == '上一页'):
            if(self.m_nCurrentPage <= 1):
                print('无上一页')
                return
            self.m_nCurrentPage -= 1
            #print(_TradePorto.m_mapPage2Res[self.m_nCurrentPage])
            btnCurrentPage.setProperty('text', '- ' + str(self.m_nCurrentPage) + ' -')
            textAreaReplyMsg.setProperty('text', _TradePorto.m_mapPage2Res[self.m_nCurrentPage][2])
            textAreaReplyData.setProperty('text', _TradePorto.m_mapPage2Res[self.m_nCurrentPage][1])
            textAreaSend.setProperty('text', _TradePorto.m_mapPage2Res[self.m_nCurrentPage][0])
        elif(btnName == '下一页'):
            #global _TradeProto
            if(self.m_nCurrentPage >= _TradePorto.m_nResCount):
                print('超出页码')
                return
            self.m_nCurrentPage += 1
            btnCurrentPage.setProperty('text', '- ' + str(self.m_nCurrentPage) + ' -')
            textAreaReplyMsg.setProperty('text', _TradePorto.m_mapPage2Res[self.m_nCurrentPage][2])
            textAreaReplyData.setProperty('text', _TradePorto.m_mapPage2Res[self.m_nCurrentPage][1])
            textAreaSend.setProperty('text', _TradePorto.m_mapPage2Res[self.m_nCurrentPage][0])
            #print(_TradePorto.m_mapPage2Res[self.m_nCurrentPage])
        else :
            print("undefined btn clicked :%s" %strContent)
            #print(self.window.findChild(QObject, "login_dialog").itemAt (3).children[1].property('text'))
            
    def __init__(self,parent=None):
        super(Main, self).__init__(parent)
        self.engine = QQmlApplicationEngine(self)
        self.engine.addImportPath("./modules")
        # 注意，在demo中，部分demo使用到了单例qml，需要使用qmldir来生效，所有需要导入demo
        # self.engine.addImportPath("./demo")
        self.engine.load(QUrl.fromLocalFile('./main.qml'))
        if len(self.engine.rootObjects()) == 0 :
            sys.exit(-1)
        #reloader = ObjectWithAReloadSignal()
        #self.engine.rootObjects().setContextProperty("_reloader", reloader)
        self.window = self.engine.rootObjects()[0]
        self.window.btnClicked.connect(self.on_click)
        #btnConnectTrade.setProperty('text', '已连接')


    def show(self):
        self.window.show()
        
app=QApplication(sys.argv)
main=Main()
textEndpoint = main.window.findChild(QObject, "login_dialog").itemAt (1).findChild(QObject, "endpoint")
btnConnectTrade = main.window.findChild(QObject, "login_dialog").itemAt (5).findChild(QObject, "连接交易")
btnConnectCommand = main.window.findChild(QObject, "login_dialog").itemAt (8).findChild(QObject, "连接命令")
textAreaReplyMsg =  main.window.findChild(QObject, "res_msg")
textAreaReplyData =  main.window.findChild(QObject, "res_data")
textAreaSend = main.window.findChild(QObject, "text_send")
btnCurrentPage = main.window.findChild(QObject,'current_res_page')
main.show()
import qt5reactor
qt5reactor.install()
from twisted.internet import reactor
sys.exit(app.exec_())


"""
import sys

def bind(objectName, propertyName, type):
    def getter(self):
        return type(self.findChild(QObject, objectName).property(propertyName).toPyObject())
    def setter(self, value):
        self.findChild(QObject, objectName).setProperty(propertyName, QVariant(value))
         
    return property(getter, setter)
"""
