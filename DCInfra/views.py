from django.http import HttpResponse
from django.shortcuts import render
from django.http import HttpResponse
import time
import subprocess
import os
from pyVim import connect
import pyrebase


config = {
    'apiKey': "AIzaSyAi3gP2MNwvzdlcvcaMuewc8zoQMDQltow",
    'authDomain': "test-3f09a.firebaseapp.com",
    'databaseURL': "https://test-3f09a.firebaseio.com",
    'projectId': "test-3f09a",
    'storageBucket': "test-3f09a.appspot.com",
    'messagingSenderId': "928354029774"
}
firebase = pyrebase.initialize_app(config)


output = subprocess.check_output(("arp", "-a"))
list1 = output.split()
ip=[]
mac=[]
l=len(list1)
i=8
while(i<l):
    if(i<l):
        s=list1[i]
        ip.append((s.decode("utf-8")).strip('(').strip(')'))
    i=i+2
    if(i<l):
        s2=list1[i]  
        mac.append(s2.decode("utf-8"))
    i=i+5


def admin_login(request):
    return render(request, "loginpage.html")


def saveStates(hostIp, num, vms):
    data={}
    for i in vms:
        nm=i.name
        state=i.summary.runtime.powerState
        data[nm]=state        
    firebase.database().child("DataCenter").child("Hosts").child(mac[num]).set(data)


def turnOffVM(hostIp,vms):
    for i in vms:
        if i.summary.runtime.powerState != 'poweredOff':            
            i.PowerOff()


def turnOffHost(hostIp, dc):
    hosts=dc.hostFolder.childEntity[0]
    state=hosts.host[0].ShutdownHost_Task(True)
    print(state)


def checkHostIsUp(hostIp):
    try:        
        my_cluster = connect.ConnectNoSSL(hostIp, 443, "root", "rootroot")
    except:
        return False
    return True


def switchToState(vm, state):
    if state == 'poweredOn':
        vm.PowerOn()
    if state == 'suspended':
        vm.PowerOn()
        time.sleep(1)
        vm.Suspend()


def turnOnVM(fbdb, hostIp):
    my_cluster= connect.ConnectNoSSL(hostIp, 443, "root", "rootroot")
    dc = my_cluster.content.rootFolder.childEntity[0]
    vms = dc.vmFolder.childEntity
    for i in vms:
        for j in fbdb:
            if i.name == j:
                print (i.name)
                print (fbdb[j])
                switchToState(i, fbdb[j])


def admin_dash_board(request):
    if (request.GET.get("mybtn")):
        #write all the code here
        rec={}
        for i in range (len(ip)):               #iterating through all the hosts             
            if checkHostIsUp(ip[i]):
                my_cluster= connect.ConnectNoSSL(ip[i], 443, "root", "rootroot")
                dc = my_cluster.content.rootFolder.childEntity[0]
                vms = dc.vmFolder.childEntity
                saveStates(ip[i], i, vms)        #saving states of the hosts to the database
                turnOffVM(ip[i], vms)            #turning off the virtual machines
                turnOffHost(ip[i], dc)          #turns the ESXi Host Off
                rec[ip[i]]=vms
        
        return render(request, "dashboard.html", {"message": "All Virtual machines powered Off Gracefully!!", 'myData':rec})
    
    if (request.GET.get('onbtn')):
        for i in range (len(ip)):            
            if checkHostIsUp(ip[i]):
                fbdb=firebase.database().child("DataCenter").child("Hosts").child(mac[i]).get().val()
                turnOnVM(fbdb, ip[i])

            else:
                return HttpResponse("Wait while the host is starting!!")

        #return (request, "dashboard.html")
        return HttpResponse("Everything Restored as it was !")

    myData={}
    for i in range (len(ip)):
        if checkHostIsUp(ip[i]):
            my_cluster= connect.ConnectNoSSL(ip[i], 443, "root", "rootroot")
            dc = my_cluster.content.rootFolder.childEntity[0]
            vms = dc.vmFolder.childEntity
            myData[ip[i]]=vms
                
    return render(request, "dashboard.html",{'myData':myData})