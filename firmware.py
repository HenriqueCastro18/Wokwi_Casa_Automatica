import gc,network,socket,machine,time,ujson
from machine import Pin,ADC,I2C,PWM
try:
 import dht
except:
 pass
try:
 from umqtt.simple import MQTTClient
 MQTT_OK=True
except:
 MQTT_OK=False
try:
 import neopixel
 NP_OK=True
except:
 NP_OK=False

class O:
 def __init__(s,i2c,a=0x3c):
  s.i=i2c;s.a=a;s.b=bytearray(1024)
  for c in [0xAE,0x20,0x00,0xB0,0xC8,0x00,0x10,0x40,0x81,0xFF,0xA1,0xA6,0xA8,0x3F,0xA4,0xD3,0x00,0xD5,0xF0,0xD9,0x22,0xDA,0x12,0xDB,0x20,0x8D,0x14,0xAF]:s.cmd(c)
 def cmd(s,c):s.i.writeto(s.a,bytes([0x00,c]))
 def fill(s,v):
  for i in range(1024):s.b[i]=0xFF if v else 0
 def px(s,x,y,c=1):
  if 0<=x<128 and 0<=y<64:
   i=(y//8)*128+x
   if c:s.b[i]|=(1<<(y%8))
   else:s.b[i]&=~(1<<(y%8))
 def text(s,t,x,y):
  for ch in t:
   c=ord(ch)
   if 32<=c<128:
    for i in range(5):
     bb=F[(c-32)*5+i]
     for j in range(8):s.px(x+i,y+j,1 if bb&(1<<j) else 0)
    x+=6
 def show(s):
  for p in range(8):
   s.cmd(0xB0+p);s.cmd(0x00);s.cmd(0x10)
   s.i.writeto(s.a,b'\x40'+bytes(s.b[p*128:(p+1)*128]))

F=bytes([0,0,0,0,0,0,0,95,0,0,0,7,0,7,0,20,127,20,127,20,36,42,127,42,18,35,19,8,100,98,54,73,85,34,80,0,5,3,0,0,0,28,34,65,0,0,65,34,28,0,8,42,28,42,8,8,8,62,8,8,0,80,48,0,0,8,8,8,8,8,0,96,96,0,0,32,16,8,4,2,62,81,73,69,62,0,66,127,64,0,66,97,81,73,70,33,65,69,75,49,24,20,18,127,16,39,69,69,69,57,60,74,73,73,48,1,113,9,5,3,54,73,73,73,54,6,73,73,41,30,0,54,54,0,0,0,86,54,0,0,8,20,34,65,0,20,20,20,20,20,0,65,34,20,8,2,1,89,9,6,62,65,93,89,78,124,18,17,18,124,127,73,73,73,54,62,65,65,65,34,127,65,65,34,28,127,73,73,73,65,127,9,9,9,1,62,65,73,73,122,127,8,8,8,127,0,65,127,65,0,32,64,65,63,1,127,8,20,34,65,127,64,64,64,64,127,2,12,2,127,127,4,8,16,127,62,65,65,65,62,127,9,9,9,6,62,65,81,33,94,127,9,25,41,70,38,73,73,73,50,3,1,127,1,3,63,64,64,64,63,31,32,64,32,31,63,64,56,64,63,99,20,8,20,99,3,4,120,4,3,97,81,73,69,67,0,127,65,65,0,2,4,8,16,32,0,65,65,127,0,4,2,1,2,4,64,64,64,64,64,0,1,2,4,0,32,84,84,84,120,127,72,68,68,56,56,68,68,68,32,56,68,68,72,127,56,84,84,84,24,8,126,9,1,2,8,20,84,84,60,127,8,4,4,120,0,68,125,64,0,32,64,68,61,0,127,16,40,68,0,0,65,127,64,0,124,4,24,4,120,124,8,4,4,120,56,68,68,68,56,124,20,20,20,8,8,20,20,24,124,124,8,4,4,8,72,84,84,84,32,4,63,68,64,32,60,64,64,32,124,28,32,64,32,28,60,64,48,64,60,68,40,16,40,68,12,80,80,80,60,68,100,84,76,68,0,8,54,65,0,0,0,127,0,0,0,65,54,8,0,8,8,42,28,8,8,28,42,8,8])

w=network.WLAN(network.STA_IF)
w.active(False);time.sleep(1.0);w.active(True);time.sleep(0.5)
WI=False
print('[WIFI]: Iniciando conexao...')
w.connect('Wokwi-GUEST','')
for _ in range(40):
 if w.isconnected():
  WI=True;break
 time.sleep(0.2)
print('WiFi:',w.ifconfig() if WI else 'FALHOU')

dp=Pin(4);ldr=ADC(Pin(34));ldr.atten(ADC.ATTN_11DB)
pot=ADC(Pin(35));pot.atten(ADC.ATTN_11DB)
try:
 gas=ADC(Pin(39));gas.atten(ADC.ATTN_11DB);GAS_OK=True
except:
 GAS_OK=False;gas=None
pir=Pin(13,Pin.IN);tr=Pin(5,Pin.OUT);ec=Pin(18,Pin.IN)
rr=PWM(Pin(12),freq=1000,duty=0);rg=PWM(Pin(16),freq=1000,duty=0);rb=PWM(Pin(17),freq=1000,duty=0)
re=Pin(32,Pin.OUT);sv=PWM(Pin(23),freq=50)
bt=PWM(Pin(25),freq=1500,duty=0)

KR=[Pin(2,Pin.OUT),Pin(15,Pin.OUT),Pin(19,Pin.OUT),Pin(33,Pin.OUT)]
KC=[Pin(26,Pin.IN,Pin.PULL_DOWN),Pin(27,Pin.IN,Pin.PULL_DOWN),Pin(14,Pin.IN,Pin.PULL_DOWN),Pin(16,Pin.IN,Pin.PULL_DOWN)]
KMAP=[['1','2','3','A'],['4','5','6','B'],['7','8','9','C'],['*','0','#','D']]
for r in KR:r.value(0)

NP=None
if NP_OK:
 try:
  NP=neopixel.NeoPixel(Pin(17),16)
  for i in range(16):NP[i]=(0,0,0)
  NP.write()
 except Exception as e:print('NeoPixel:',e);NP=None

OK=False;oled=None
try:
 i2c=I2C(0,scl=Pin(22),sda=Pin(21),freq=400000);time.sleep_ms(100)
 dv=i2c.scan();print('I2C:',[hex(x) for x in dv])
 if dv:oled=O(i2c,dv[0]);oled.fill(0);oled.text('Casa IoT',30,28);oled.show();OK=True
except Exception as e:print('OLED:',e)

st={'alerta':False,'rele':False,'porta':0,'porta_aberta':False,'buz_temp':False,'temp':0,'hum':0,'luz':0,'pot':0,'gas':0,'limite':30.0,'mov':0,'dist':0,'wifi':WI,'mqtt':False,'oled':OK,'kp_buf':'','kp_msg':'Digite a senha','sistema_armado':False,'tentativas_erradas':0,'entrada_bloqueada':False}

SENHA='1234'
v_temp=-1.0
t_alarme=0
em_espera=False
ring_idx=0
last_ring=0
porta_t=0
t_bloqueio=0
last_key=''
last_key_t=0

def beep_curto(dur=100):
 bt.duty(512)
 time.sleep_ms(dur)
 bt.duty(0)

def dh():
 try:
  import dht;d=dht.DHT22(dp);d.measure();return d.temperature(),d.humidity()
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

def scan_kp():
 global last_key,last_key_t
 now=time.ticks_ms()
 if time.ticks_diff(now,last_key_t)<50:return None
 for ri in range(4):
  for rr2 in KR:rr2.value(0)
  KR[ri].value(1)
  time.sleep_us(50)
  for ci in range(4):
   if KC[ci].value():
    k=KMAP[ri][ci]
    last_key=k;last_key_t=now
    KR[ri].value(0)
    beep_curto(80)
    return k
  KR[ri].value(0)
 return None

def proc_kp(k):
 global porta_t,t_bloqueio
 if k is None:return
 print('[KEYPAD]:',k)
 if k=='*':
  if st['entrada_bloqueada']:
   if time.ticks_diff(time.ticks_ms(),t_bloqueio)>=30000:
    st['entrada_bloqueada']=False
    st['tentativas_erradas']=0
    st['kp_msg']='Desbloqueado'
   return
  st['kp_buf']='';st['kp_msg']='Limpo'
 elif k=='#':
  if st['entrada_bloqueada']:return
  if st['kp_buf']==SENHA:
   st['porta']=90;st['porta_aberta']=True;porta_t=time.ticks_ms()
   st['sistema_armado']=False
   st['tentativas_erradas']=0
   st['kp_msg']='PORTA ABERTA!';st['kp_buf']=''
  else:
   st['tentativas_erradas']+=1
   if st['tentativas_erradas']<3:
    dur=500 if st['tentativas_erradas']==1 else 700
    beep_curto(dur)
    st['kp_msg']='Errada ('+str(st['tentativas_erradas'])+'/3)'
   else:
    st['alerta']=True
    st['buz_temp']=True
    st['entrada_bloqueada']=True
    t_bloqueio=time.ticks_ms()
    st['kp_msg']='BLOQUEADO 30s'
   st['kp_buf']=''
 elif k in '0123456789':
  if not st['entrada_bloqueada'] and len(st['kp_buf'])<4:
   st['kp_buf']+=k;st['kp_msg']='Digitando...'

def update_ring():
 global ring_idx,last_ring
 if NP is None:return
 now=time.ticks_ms()
 if time.ticks_diff(now,last_ring)<80:return
 last_ring=now
 if st['alerta']:
  for i in range(16):
   d=(i-ring_idx)%16
   if d<4:
    b=int(80*(1-d/4.0))
    NP[i]=(b,0,0)
   else:
    NP[i]=(0,0,0)
  ring_idx=(ring_idx+1)%16
 elif em_espera:
  for i in range(16):NP[i]=(40,20,0) if ((i+ring_idx)%2==0) else (0,0,0)
  ring_idx=(ring_idx+1)%16
 else:
  for i in range(16):NP[i]=(0,0,0)
 try:NP.write()
 except:pass

def ap():
 re.value(st['rele'])
 sv.duty(int(26+(st['porta']/180)*102))
 bt.duty(512 if st['buz_temp'] else 0)
 if st['alerta']:rr.duty(1023);rg.duty(0);rb.duty(0)
 elif st['mov']:rr.duty(0);rg.duty(0);rb.duty(1023)
 elif st['rele']:rr.duty(1023);rg.duty(600);rb.duty(0)
 elif st['porta_aberta']:rr.duty(0);rg.duty(800);rb.duty(800)
 else:rr.duty(0);rg.duty(1023);rb.duty(0)

def uo():
 if not OK:return
 try:
  oled.fill(0);oled.text('CASA IoT',0,0)
  if st['alerta']:oled.text('ALERT',80,0)
  elif st['rele']:oled.text('AR ON',80,0)
  elif st['porta_aberta']:oled.text('OPEN',90,0)
  oled.text('T:'+str(round(st['temp'],1))+'C L:'+str(int(st['limite'])),0,12)
  oled.text('Luz:'+str(st['luz'])+' G:'+str(st['gas']),0,24)
  oled.text('Mov:'+('S' if st['mov'] else 'N')+' D:'+str(int(st['dist']))+'cm',0,36)
  oled.text('Key:'+st['kp_buf'].ljust(4,'_'),0,48)
  oled.show()
 except:pass

def al():
 return [
  {'nome':'Temperatura Alta','cond':'Temp > '+str(int(st['limite']))+' C','atual':str(round(st['temp'],1))+' C','ativo':st['temp']>st['limite']},
  {'nome':'Pouca Luz','cond':'Luminosidade < 500','atual':str(st['luz']),'ativo':0<st['luz']<500},
  {'nome':'Movimento Detectado','cond':'PIR ativo','atual':'Sim' if st['mov'] else 'Nao','ativo':st['mov']==1 and st['sistema_armado']},
  {'nome':'Objeto Proximo','cond':'Distancia < 30 cm','atual':str(int(st['dist']))+' cm','ativo':0<st['dist']<30 and st['sistema_armado']},
  {'nome':'Gas Detectado','cond':'Gas > 3800','atual':str(st['gas']),'ativo':st['gas']>3800}
 ]

def cb(t,m):
 try:
  t=t.decode();m=m.decode();print('[MQTT RCV]:',t,m);k=t.split('/')[-1]
  if k in ['alerta','rele','buz_temp']:st[k]=(m=='1')
  elif k=='porta':
   try:st['porta']=int(m);st['porta_aberta']=(st['porta']>0)
   except:pass
  ap()
 except Exception as e:print('Erro callback:',e)

def conectar_mqtt():
 try:
  print('[MQTT]: Conectando...')
  m_cli=MQTTClient('esp32h_'+str(time.ticks_ms()),'broker.hivemq.com',1883,keepalive=60)
  m_cli.set_callback(cb);m_cli.connect()
  for tp in ['casa/henrique/alerta','casa/henrique/rele','casa/henrique/buz_temp','casa/henrique/porta']:m_cli.subscribe(tp)
  print('[MQTT]: Conectado!');return m_cli
 except Exception as e:print('[MQTT Erro]:',e);return None

mq=None
if MQTT_OK and WI:mq=conectar_mqtt();st['mqtt']=(mq is not None)

sv2=socket.socket();sv2.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
sv2.bind(('',80));sv2.listen(5);sv2.settimeout(0)

try:
 with open('page.html') as f:PG=f.read()
except:
 PG='<h1>page.html nao encontrado</h1>'

ap();uo();lp=0;ls2=0

def resp(c,body,ct='text/html'):
 try:
  if isinstance(body,str):body=body.encode()
  h='HTTP/1.1 200 OK\r\nContent-Type: '+ct+'\r\nContent-Length: '+str(len(body))+'\r\nConnection: close\r\nAccess-Control-Allow-Origin: *\r\n\r\n'
  c.sendall(h.encode()+body)
 except:pass

while True:
 WI=w.isconnected();st['wifi']=WI
 k=scan_kp()
 if k:proc_kp(k)
 if st['entrada_bloqueada'] and time.ticks_diff(time.ticks_ms(),t_bloqueio)>=30000:
  st['entrada_bloqueada']=False
  st['tentativas_erradas']=0
  st['kp_msg']='Desbloqueado'
 if st['porta_aberta'] and time.ticks_diff(time.ticks_ms(),porta_t)>5000:
  st['porta']=0;st['porta_aberta']=False;st['kp_msg']='Porta fechada';ap()
 update_ring()
 try:
  c,_=sv2.accept();c.settimeout(0.3)
  try:
   r=c.recv(2048)
   if r:
    rs=r.decode('utf-8','ignore')
    p='/'
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
      if v>0:porta_t=time.ticks_ms()
     except:pass
     ap();resp(c,'ok','text/plain')
    else:resp(c,PG,'text/html')
  except:pass
  finally:
   try:c.close()
   except:pass
 except OSError:pass

 if time.ticks_diff(time.ticks_ms(),ls2)>1500:
  ls2=time.ticks_ms()
  real_t,h=dh();st['hum']=h
  st['luz']=ldr.read();st['pot']=pot.read();st['mov']=pir.value();st['dist']=us()
  if GAS_OK:
   try:st['gas']=gas.read()
   except:st['gas']=0
  st['limite']=20.0+(st['pot']/4095.0)*20.0
  if st['gas']>3800:
   st['rele']=False
  if v_temp<0:v_temp=real_t
  if st['rele']:
   if v_temp>(st['limite']-1.0):v_temp-=0.5
   else:st['rele']=False
  else:
   if em_espera:
    if time.ticks_diff(time.ticks_ms(),t_alarme)>=1500:
     st['rele']=True;em_espera=False;st['alerta']=False
   else:
    if v_temp<(st['limite']+5.0):
     v_temp+=0.1
     if v_temp>real_t:v_temp=real_t
    else:
     em_espera=True;t_alarme=time.ticks_ms();st['alerta']=True
  st['temp']=v_temp
  st['buz_temp']=em_espera
  if not em_espera:
   st['alerta']=(st['mov']==1 and 0<st['dist']<30 and st['sistema_armado']) or (st['gas']>3800) or (st['temp']>(st['limite']+5.0) and not st['rele'])
  ap();uo();print('T:',round(st['temp'],1),'G:',st['gas'],'K:',st['kp_buf'],'ARM:',st['sistema_armado'],'S:','EMERG' if em_espera else ('AR' if st['rele'] else 'OK'))

 if time.ticks_diff(time.ticks_ms(),lp)>5000:
  lp=time.ticks_ms()
  if not WI:
   try:w.connect('Wokwi-GUEST','')
   except:pass
  elif mq:
   try:mq.publish('casa/henrique/status',ujson.dumps(st));mq.check_msg();st['mqtt']=True
   except:st['mqtt']=False;mq=None
  elif MQTT_OK:mq=conectar_mqtt();st['mqtt']=(mq is not None)
 time.sleep_ms(10)
