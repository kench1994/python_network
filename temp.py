# -*- coding: utf-8 -*-

from twisted.internet.protocol import ServerFactory
from twisted.protocols.basic import LineReceiver
from twisted.internet import reactor, threads, defer
import functools
import json

PORT = 7708

class CmdProtocol(LineReceiver):
    client_ip = ''
    client_port = 0
    # 连接建立接口
    def connectionMade(self):
    # 获得连接对端 ip
        self.client_ip = self.transport.getPeer().host
        self.client_port = self.transport.getPeer().port
        print("Client connection from %s : %d" % (self.client_ip, self.client_port))
  
    #进行多连接控制
        if len(self.factory.clients) >= self.factory.clients_max:
            print("Too many connections. Disconnect!")
            self.client_ip = None
            self.transport.loseConnenction()
        else:
            self.factory.clients.append(self.client_ip)
            
    # 连接断开接口
        def connectionLost(self, reason):
            print('Lost client connection. Reason: %s' % reason)
    #连接断开接口
    def connectionLost(self, reason):
        print("Lost connection. Reason: %s" % reason)
                  
    
    
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
        print("current parse buffer:%s" %parse_buffer)
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
        
    
    def package_demultiplex(self, single_package) : 
        try : 
            json_object = json.loads(single_package)
            action = json_object['action']
            print ('Current action : %s' % action)
        except : 
            print ("package raw data : %s" % single_package)
    
    
    # 数据接收接口
    def dataReceived(self, recv_data):
        recv_data = recv_data.decode("UTF-8")
        #self.package_demultiplex(recv_data.decode("UTF-8"))
        #定义一个是否接受数据的标识
        recv_length = len(recv_data)
        while 1:
            (resume_data_size, tcp_package) = self.package_retriver(recv_data, recv_length)

            if resume_data_size == -2 :
                #未完成继续接收
                return
            elif resume_data_size == -1 :
                #解析发生错误,关闭连接
                print ('解析发生错误,关闭连接')
                self.transport.abortConnection()
            #do biz action here
            #self.package_demultiplex(tcp_package)
            # d = threads.deferToThread(functools.partial(self.package_demultiplex, tcp_package))
            # d.addCallback(self.send_response)
            self.package_demultiplex(tcp_package)
            self.send_response(tcp_package);
            
            #缓存已解析完毕
            if resume_data_size == 0 :
                break
            
            #print "Enter Unexcepted Handler"
            recv_data = ''
            recv_length = 0
        
    def send_response(self, response_data) :
        self.transport.write(response_data + "\n")       
            
class RPCFactory(ServerFactory):
    # 使用 CmdProtocol 与客户端通信
    protocol = CmdProtocol
    
    #设置最大连接数
    def __init__(self, clients_max = 65535):
        self.clients_max = clients_max
        self.clients = []
        
# 启动服务器
if __name__ == "__main__":
    
    reactor.listenTCP(PORT, RPCFactory())
    reactor.run()