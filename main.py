import network,socket,machine,time,ujson,gc
from machine import Pin,ADC,I2C,PWM

try:
 import dht
except:
 pass

w=network.WLAN(network.STA_IF)
w.active(False);time.sleep(1.0);w.active(True);time.sleep(0.5)
WI=False
print("[WIFI]: Iniciando conexao...")
w.connect("Wokwi-GUEST","")
for _ in range(40):
 if w.isconnected():
  WI=True;break
 time.sleep(0.2)
print("WiFi:",w.ifconfig() if WI else "FALHOU")

dp=Pin(4);ldr=ADC(Pin(34));ldr.atten(ADC.ATTN_11DB)
pot=ADC(Pin(35));pot.atten(ADC.ATTN_11DB)
try:
 gas=ADC(Pin(39));gas.atten(ADC.ATTN_11DB);GAS_OK=True
except:
 GAS_OK=False;gas=None
pir=Pin(13,Pin.IN);tr=Pin(5,Pin.OUT);ec=Pin(18,Pin.IN)
rr=PWM(Pin(14),freq=1000,duty=0);rg=PWM(Pin(26),freq=1000,duty=0);rb=PWM(Pin(27),freq=1000,duty=0)
re=Pin(32,Pin.OUT);sv=PWM(Pin(23),freq=50)
bt=PWM(Pin(25),freq=1500,duty=0)

OK=False;oled=None
try:
 i2c=I2C(0,scl=Pin(22),sda=Pin(21),freq=400000);time.sleep_ms(100)
 dv=i2c.scan();print("I2C:",[hex(x) for x in dv])
 if dv:
  from firmware import O
  oled=O(i2c,dv[0]);oled.fill(0);oled.text("Casa IoT",30,28);oled.show();OK=True
except Exception as e:print("OLED:",e)

st={'alerta':False,'rele':False,'porta':0,'porta_aberta':False,'buz_temp':False,'temp':0,'hum':0,'luz':0,'pot':0,'gas':0,'limite':30.0,'mov':0,'dist':0,'wifi':WI,'mqtt':False,'oled':OK,'luz_quarto':False,'luz_sala':False}

v_temp=-1.0;t_alarme=0;em_espera=False

def dh():
 try:import dht;d=dht.DHT22(dp);d.measure();return d.temperature(),d.humidity()
 except:return 0,0

def us():
 tr.value(0);time.sleep_us(2)
 tr.value(1);time.sleep_us(10);tr.value(0)
 try:
  from machine import time_pulse_us
  d=time_pulse_us(ec,1,30000)
  if d<0:return 0
  dc=d/58.2
  return dc if 2<=dc<=400 else 0
 except:return 0

def ap():
 re.value(st['rele'])
 sv.duty(int(26+(st['porta']/180)*102))
 if st['alerta']:
  rr.duty(0);rg.duty(1023);rb.duty(1023)
  bt.freq(1500);bt.duty(512)
 elif st['luz_sala']:
  rr.duty(0);rg.duty(0);rb.duty(1023)
  bt.duty(0)
 elif st['luz_quarto']:
  rr.duty(1023);rg.duty(0);rb.duty(1023)
  bt.duty(0)
 else:
  rr.duty(1023);rg.duty(1023);rb.duty(1023)
  bt.duty(0)

def uo():
 if not OK:return
 try:
  from firmware import O
  oled.fill(0);oled.text("CASA IoT",0,0)
  if st['alerta']:oled.text("ALERT",80,0)
  elif st['rele']:oled.text("AR ON",80,0)
  oled.text("T:"+str(round(st['temp'],1))+"C L:"+str(int(st['limite'])),0,12)
  oled.text("G:"+str(st['gas'])+" M:"+str(st['mov'])+" D:"+str(int(st['dist'])),0,24)
  oled.show()
 except:pass

def al():
 return [
  {'nome':'Temp Alta','cond':'T>'+str(int(st['limite']))+'C','atual':str(round(st['temp'],1))+'C','ativo':st['temp']>st['limite']},
  {'nome':'Pouca Luz','cond':'Luz<500','atual':str(st['luz']),'ativo':0<st['luz']<500},
  {'nome':'Movimento','cond':'PIR ativo','atual':'Sim' if st['mov'] else 'Nao','ativo':st['mov']==1},
  {'nome':'Objeto Proximo','cond':'Dist<30cm','atual':str(int(st['dist']))+'cm','ativo':0<st['dist']<30},
  {'nome':'Gas','cond':'G>3800','atual':str(st['gas']),'ativo':st['gas']>3800}
 ]

sv2=socket.socket();sv2.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
sv2.bind(('',80));sv2.listen(5);sv2.settimeout(0)

ap();uo();lp=0;ls2=0

def resp(c,body,ct='text/html'):
 try:
  if isinstance(body,str):body=body.encode()
  h='HTTP/1.1 200 OK\r\nContent-Type: '+ct+'\r\nContent-Length: '+str(len(body))+'\r\nConnection: close\r\nAccess-Control-Allow-Origin: *\r\n\r\n'
  c.sendall(h.encode()+body)
 except:pass

while True:
 WI=w.isconnected();st['wifi']=WI
 try:
  c,_=sv2.accept();c.settimeout(0.01)
  try:
   r=c.recv(1024)
   if r:
    rs=r.decode('utf-8','ignore');p='/'
    if ' ' in rs:p=rs.split(' ')[1]
    if p=='/api/data':
     d=dict(st);d['alarmes']=al()
     resp(c,ujson.dumps(d),'application/json')
    elif p.startswith('/t/'):
     kk=p[3:].split('?')[0].split(' ')[0]
     if kk in st and isinstance(st[kk],bool):st[kk]=not st[kk]
     ap();resp(c,'ok','text/plain')
    elif p.startswith('/porta/'):
     try:
      v=int(p[7:].split('?')[0].split(' ')[0])
      st['porta']=v;st['porta_aberta']=(v>0)
     except:pass
     ap();resp(c,'ok','text/plain')
    else:
     try:
      c.sendall(b'HTTP/1.1 200 OK\r\nContent-Type: text/html\r\nConnection: close\r\n\r\n')
      with open('page.html','rb') as f:
       while True:
        chunk=f.read(512)
        if not chunk:break
        c.sendall(chunk)
     except:c.sendall(b'HTTP/1.1 500\r\n\r\nErro')
  except:pass
  finally:
   try:c.close()
   except:pass
 except OSError:pass

 if time.ticks_diff(time.ticks_ms(),ls2)>1500:
  ls2=time.ticks_ms()
  real_t,h=dh();st['hum']=h;st['luz']=ldr.read();st['pot']=pot.read();st['mov']=pir.value();st['dist']=us()
  if GAS_OK:
   try:st['gas']=gas.read()
   except:st['gas']=0
  st['limite']=20.0+(st['pot']/4095.0)*20.0
  if v_temp<0:v_temp=real_t
  if st['rele']:
   if v_temp>(st['limite']-1.0):v_temp-=0.5
   else:st['rele']=False
  else:
   if em_espera:
    if time.ticks_diff(time.ticks_ms(),t_alarme)>=1500:st['rele']=True;em_espera=False;st['alerta']=False
   else:
    if v_temp<(st['limite']+5.0):v_temp+=0.1;v_temp=real_t if v_temp>real_t else v_temp
    else:em_espera=True;t_alarme=time.ticks_ms();st['alerta']=True
  st['temp']=v_temp;st['buz_temp']=em_espera
  if not em_espera:st['alerta']=(st['mov']==1 and 0<st['dist']<30) or (st['gas']>3800) or (st['temp']>(st['limite']+5.0) and not st['rele'])
  ap();uo()
  gc.collect()

 time.sleep_ms(5)
