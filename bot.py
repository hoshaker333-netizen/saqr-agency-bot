import os,re,uuid,sqlite3,logging
from decimal import Decimal,ROUND_HALF_UP
import aiohttp
from telegram import Update,InlineKeyboardButton,InlineKeyboardMarkup,ReplyKeyboardMarkup
from telegram.ext import Application,CommandHandler,CallbackQueryHandler,MessageHandler,ContextTypes,filters

logging.basicConfig(level=logging.INFO,format='%(asctime)s %(levelname)s %(message)s')
BOT_TOKEN=os.getenv('BOT_TOKEN','').strip(); ALKABOS_API_KEY=os.getenv('ALKABOS_API_KEY','').strip(); XPRO_API_KEY=os.getenv('XPRO_API_KEY','').strip()
ADMIN_ID=int(os.getenv('ADMIN_ID','0') or 0); PAYMENT_NAME=os.getenv('PAYMENT_NAME','Hosam Shaker'); PAYMENT_METHOD=os.getenv('PAYMENT_METHOD','Vodafone Cash'); PAYMENT_NUMBER=os.getenv('PAYMENT_NUMBER','')
MARGIN=Decimal(os.getenv('PROFIT_MARGIN','70') or '70'); FALLBACK=Decimal(os.getenv('FALLBACK_USD_EGP','51.36') or '51.36')
ALK='https://alkabos.com/api/v2'; XPRO='https://xprostore.store/api/v1'; DB='/data/bot.db'
IDS={'4630','824','826','4380','856','3322','1234','4577','4571','341','4357','3288','3805','3803','4631','4632','3321','2597','4299','4564','3400','3366','3395','3396','3397','3398','3399','2774','2775','2776','2777','3246','2623','4383','3239','1737','3559','3560','806','807','4308','4309','2545','2077','3678','1532','1340','1809','3237','4530','4531','4532','4533','4318','4319','4465','4281'}
MAIN=[['💻 البرامج والاشتراكات','📱 السوشيال ميديا والماركتينج'],['📦 طلباتي','🎧 الدعم']]
SOCIAL=['📸 Instagram','🎵 TikTok','🔵 Facebook','▶️ YouTube','✈️ Telegram','🟢 WhatsApp','𝕏 X / Twitter','👻 Snapchat','🎮 Twitch','💼 LinkedIn','🌐 المواقع والمتاجر','📢 التسويق والإعلانات']

def db():
 c=sqlite3.connect(DB); c.row_factory=sqlite3.Row; return c

def init_db():
 os.makedirs('/data',exist_ok=True); c=db(); c.execute('''CREATE TABLE IF NOT EXISTS orders(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER,username TEXT,provider TEXT DEFAULT '',service_id TEXT DEFAULT '',service_name TEXT DEFAULT '',category TEXT DEFAULT '',link TEXT DEFAULT '',quantity INTEGER DEFAULT 0,cost REAL DEFAULT 0,sale_price REAL DEFAULT 0,payment_status TEXT DEFAULT 'pending',order_status TEXT DEFAULT 'awaiting_payment',provider_order_id TEXT DEFAULT '',proof_file_id TEXT DEFAULT '',created_at TEXT DEFAULT CURRENT_TIMESTAMP)''')
 cols={x['name'] for x in c.execute('PRAGMA table_info(orders)')}; add={'provider':'TEXT DEFAULT \'\'','service_id':'TEXT DEFAULT \'\'','service_name':'TEXT DEFAULT \'\'','category':'TEXT DEFAULT \'\'','link':'TEXT DEFAULT \'\'','quantity':'INTEGER DEFAULT 0','cost':'REAL DEFAULT 0','sale_price':'REAL DEFAULT 0','payment_status':'TEXT DEFAULT \'pending\'','order_status':'TEXT DEFAULT \'awaiting_payment\'','provider_order_id':'TEXT DEFAULT \'\'','proof_file_id':'TEXT DEFAULT \'\''}
 for k,v in add.items():
  if k not in cols: c.execute(f'ALTER TABLE orders ADD COLUMN {k} {v}')
 c.commit(); c.close()

async def request(url,method='POST',data=None,json=None,headers=None):
 async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=25)) as s:
  async with s.request(method,url,data=data,json=json,headers=headers) as r:
   t=await r.text()
   try: import json as j; return j.loads(t)
   except: return {'error':f'HTTP {r.status}: {t[:500]}'}

async def alk(action,**kw): return await request(ALK,data={'key':ALKABOS_API_KEY,'action':action,**kw})
async def alk_services(): return await alk('services')
async def alk_add(sid,link,q): return await alk('add',service=sid,link=link,quantity=q)
async def alk_balance(): return await alk('balance')
async def xservices(): return await request(XPRO,method='GET',headers={'Authorization':f'Bearer {XPRO_API_KEY}'})
async def xorder(sid,q): return await request(XPRO+'/orders',json={'service_id':str(sid),'quantity':int(q)},headers={'Authorization':f'Bearer {XPRO_API_KEY}','Content-Type':'application/json','Idempotency-Key':str(uuid.uuid4())})
async def fx():
 for u in ['https://api.frankfurter.dev/v2/providers/cbe/rate/usd/egp','https://api.frankfurter.dev/v2/rate/usd/egp']:
  try:
   d=await request(u,method='GET');
   if d.get('rate'): return Decimal(str(d['rate']))
  except: pass
 return FALLBACK

def money(x): return Decimal(str(x)).quantize(Decimal('.01'),rounding=ROUND_HALF_UP)
def price(rate,q,ratefx):
 cost=Decimal(str(rate))*Decimal(str(q))/Decimal(1000)*ratefx; return money(cost),money(cost*(1+MARGIN/100))
def plat(s):
 t=str(s).lower(); mp=[('Instagram',['instagram','انستجرام','انستغرام','انستا']),('TikTok',['tiktok','تيك توك','تيكتوك']),('Facebook',['facebook','فيسبوك','فيس بوك']),('YouTube',['youtube','يوتيوب']),('Telegram',['telegram','تيليجرام','تلجرام']),('WhatsApp',['whatsapp','واتساب','واتس']),('X / Twitter',['twitter','تويتر']),('Snapchat',['snapchat','سناب']),('Twitch',['twitch']),('LinkedIn',['linkedin','لينكد'])]
 for p,ws in mp:
  if any(w in t for w in ws): return p
 return 'أخرى'
def typ(s):
 t=str(s).lower(); mp=[('👥 متابعين',['follower','متابع']),('❤️ لايكات',['like','لايك','اعجاب','إعجاب']),('👀 مشاهدات',['view','مشاهد']),('💬 تعليقات',['comment','تعليق']),('🔄 مشاركات',['share','مشاركة']),('🔖 حفظ',['save','حفظ']),('📢 وصول',['reach','وصول']),('⏱️ وقت مشاهدة',['watch time','وقت مشاهدة'])]
 for a,ws in mp:
  if any(w in t for w in ws): return a
 return '🛠️ خدمات أخرى'
def pname(s): return f'{typ(s)} — {plat(s)}' if plat(s)!='أخرى' and typ(s)!='🛠️ خدمات أخرى' else str(s).strip()
def pcat(n):
 t=str(n).lower(); rules=[('🤖 الذكاء الاصطناعي',['chatgpt','gemini','claude','perplexity','copilot',' ai']),('🎬 المونتاج والفيديو',['capcut','premiere','filmora','video']),('🎨 التصميم والجرافيك',['canva','photoshop','illustrator','design','adobe']),('🎵 الصوت والموسيقى',['spotify','music','audio']),('📝 الإنتاجية والعمل',['notion','microsoft','office','miro','grammarly','ilovepdf']),('📚 التعليم والكورسات',['course','education','udemy']),('🔐 VPN والأمان',['vpn','security']),('🎞️ الترفيه والمنصات',['netflix','hbo','max','peacock','paramount','disney'])]
 for c,ws in rules:
  if any(w in t for w in ws): return c
 return '🧰 أدوات وخدمات متنوعة'
def arr(d):
 if isinstance(d,list): return d
 if isinstance(d,dict): return d.get('services') or d.get('data') or d.get('results') or []
 return []
async def socials(): return [s for s in arr(await alk_services()) if str(s.get('service','')) in IDS]
async def programs(): return arr(await xservices())
def main_kb(): return ReplyKeyboardMarkup(MAIN,resize_keyboard=True)

def save(uid,user,provider,s,link,q,cost,sale):
 c=db(); cur=c.execute('INSERT INTO orders(user_id,username,provider,service_id,service_name,category,link,quantity,cost,sale_price) VALUES(?,?,?,?,?,?,?,?,?,?)',(uid,user,provider,s['service_id'],s['service_name'],s.get('category',''),link,q,float(cost),float(sale))); oid=cur.lastrowid; c.commit(); c.close(); return oid

async def start(u,c): c.user_data.clear(); await u.message.reply_text('أهلاً بيك في SaQr Agency 🦅\n\nاختار الخدمة:',reply_markup=main_kb())
async def social_menu(u,c):
 kb=[]; row=[]
 for i,x in enumerate(SOCIAL):
  row.append(InlineKeyboardButton(x,callback_data=f'sc:{i}'))
  if len(row)==2: kb.append(row); row=[]
 if row: kb.append(row)
 kb.append([InlineKeyboardButton('🔙 الرئيسية',callback_data='home')]); await u.message.reply_text('📱 اختر المنصة:',reply_markup=InlineKeyboardMarkup(kb))
async def social_list(q,c,platform):
 ss=[s for s in await socials() if plat(s.get('name'))==platform]
 if not ss: await q.message.edit_text('لا توجد خدمات مضافة لهذه المنصة حاليًا.'); await q.answer(); return
 kb=[[InlineKeyboardButton(pname(s.get('name'))[:60],callback_data=f's:{s.get("service")}')] for s in ss]; kb.append([InlineKeyboardButton('🔙 المنصات',callback_data='socials')]); await q.message.edit_text(f'📱 {platform}\n\nاختر الخدمة:',reply_markup=InlineKeyboardMarkup(kb)); await q.answer()
async def social_detail(q,c,sid):
 s=next((x for x in await socials() if str(x.get('service'))==str(sid)),None)
 if not s: await q.answer('الخدمة غير موجودة'); return
 rate=await fx(); cost,sale=price(s.get('rate','0'),1000,rate); c.user_data['sel']={'provider':'alkabos','service_id':str(sid),'service_name':pname(s.get('name')),'category':plat(s.get('name')),'min':int(float(s.get('min') or 1)),'max':int(float(s.get('max') or 0)),'cost1000':str(cost),'sale1000':str(sale)}
 refill='30 يوم' if s.get('refill') else 'غير متاح'; txt=f'📌 {pname(s.get("name"))}\n\n⏱️ البدء: 0–1 ساعة\n🔄 الجودة: حسب الخدمة\n🛡️ الضمان: {refill}\n\n🔢 الحد الأدنى: {int(float(s.get("min") or 1)):,}\n💰 السعر: {sale:,.2f} ج لكل 1000'
 await q.message.edit_text(txt,reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('🛒 طلب الخدمة',callback_data='sorder')],[InlineKeyboardButton('🔙 الخدمات',callback_data='socials')]])); await q.answer()
async def programs_menu(u,c):
 if not XPRO_API_KEY: await u.message.reply_text('💻 البرامج والاشتراكات\n\nX Pro Store غير مربوط حاليًا.',reply_markup=main_kb()); return
 ps=await programs(); cats={}
 for s in ps: cats[pcat(s.get('name') or s.get('title') or '')]=cats.get(pcat(s.get('name') or s.get('title') or ''),0)+1
 kb=[[InlineKeyboardButton(f'{k} ({v})',callback_data=f'pc:{k}')] for k,v in cats.items()]; kb.append([InlineKeyboardButton('🔙 الرئيسية',callback_data='home')]); await u.message.reply_text('💻 البرامج والاشتراكات\n\nاختر القسم:',reply_markup=InlineKeyboardMarkup(kb))
async def program_list(q,c,cat):
 ss=[s for s in await programs() if pcat(s.get('name') or s.get('title') or '')==cat]; kb=[]
 for s in ss:
  sid=str(s.get('id') or s.get('service_id') or s.get('service')); name=str(s.get('name') or s.get('title') or 'خدمة'); kb.append([InlineKeyboardButton(name[:60],callback_data=f'p:{sid}')])
 kb.append([InlineKeyboardButton('🔙 الأقسام',callback_data='programs')]); await q.message.edit_text(f'{cat}\n\nاختر الخدمة:',reply_markup=InlineKeyboardMarkup(kb)); await q.answer()
def xprice(s):
 for k in ('price','rate','amount','selling_price','unit_price'):
  if s.get(k) not in (None,''):
   try:return money(s[k])
   except:pass
 return Decimal('0')
async def program_detail(q,c,sid):
 s=next((x for x in await programs() if str(x.get('id') or x.get('service_id') or x.get('service'))==str(sid)),None)
 if not s: await q.answer('الخدمة غير موجودة'); return
 name=str(s.get('name') or s.get('title') or 'خدمة'); c.user_data['sel']={'provider':'xpro','service_id':str(sid),'service_name':name,'category':pcat(name),'unit':str(xprice(s))}; await q.message.edit_text(f'📌 {name}\n\n💰 السعر: {xprice(s):,.2f} ج\n\nاختار طلب الخدمة:',reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('🛒 طلب الخدمة',callback_data='porder')],[InlineKeyboardButton('🔙 البرامج',callback_data='programs')]])); await q.answer()
async def ask_qty(q,c): c.user_data['step']='qty'; await q.message.reply_text('🔢 اكتب الكمية المطلوبة:'); await q.answer()
async def text(u,c):
 if c.user_data.get('proof') and u.message.photo:
  oid=c.user_data.pop('proof'); fid=u.message.photo[-1].file_id; dbx=db(); dbx.execute("UPDATE orders SET proof_file_id=?,payment_status='proof_submitted',order_status='awaiting_admin' WHERE id=?",(fid,oid)); row=dbx.execute('SELECT * FROM orders WHERE id=?',(oid,)).fetchone(); dbx.commit(); dbx.close();
  if ADMIN_ID: await c.bot.send_photo(ADMIN_ID,fid,caption=f'🧾 إثبات دفع جديد\nالطلب #{oid}\nالخدمة: {row["service_name"]}\nالكمية: {row["quantity"]}\nالمبلغ: {row["sale_price"]:,.2f} ج',reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('✅ قبول',callback_data=f'a:{oid}'),InlineKeyboardButton('❌ رفض',callback_data=f'r:{oid}')]]))
  await u.message.reply_text('✅ تم استلام إثبات الدفع وسيتم مراجعته.',reply_markup=main_kb()); return
 t=(u.message.text or '').strip(); step=c.user_data.get('step')
 if t=='💻 البرامج والاشتراكات': c.user_data.clear(); await programs_menu(u,c); return
 if t=='📱 السوشيال ميديا والماركتينج': c.user_data.clear(); await social_menu(u,c); return
 if t=='📦 طلباتي': await orders(u,c); return
 if t=='🎧 الدعم': await u.message.reply_text('🎧 الدعم\n\nابعت رقم الطلب ومشكلتك.',reply_markup=main_kb()); return
 if step=='link': c.user_data['link']=t; c.user_data['step']='qty'; await u.message.reply_text(f'🔢 اكتب الكمية.\nالحد الأدنى: {c.user_data["sel"]["min"]:,}'); return
 if step=='qty':
  try:q=int(t)
  except: await u.message.reply_text('❌ اكتب رقمًا صحيحًا.'); return
  s=c.user_data['sel'];
  if s['provider']=='alkabos':
   if q<s['min']: await u.message.reply_text(f'❌ أقل كمية: {s["min"]:,}'); return
   if s['max'] and q>s['max']: await u.message.reply_text('❌ الكمية أكبر من الحد المسموح.'); return
   sale=money(Decimal(s['sale1000'])*q/1000); cost=money(Decimal(s['cost1000'])*q/1000)
  else: sale=money(Decimal(s['unit'])*q); cost=sale
  c.user_data.update(q=q,sale=str(sale),cost=str(cost)); c.user_data['step']='confirm'; await u.message.reply_text(f'🧾 ملخص الطلب\n\n📌 الخدمة: {s["service_name"]}\n🔗 الرابط: {c.user_data.get("link", "—")}\n🔢 الكمية: {q:,}\n💰 التكلفة: {sale:,.2f} ج\n\nتأكيد؟',reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('✅ تأكيد الطلب',callback_data='confirm')],[InlineKeyboardButton('❌ إلغاء',callback_data='cancel')]])); return
 await u.message.reply_text('اختار من القائمة الرئيسية:',reply_markup=main_kb())
async def orders(u,c):
 d=db(); rs=d.execute('SELECT * FROM orders WHERE user_id=? ORDER BY id DESC LIMIT 10',(u.effective_user.id,)).fetchall(); d.close();
 if not rs: await u.message.reply_text('📦 لا توجد طلبات حتى الآن.',reply_markup=main_kb()); return
 await u.message.reply_text('\n\n'.join([f'#{r["id"]} — {r["service_name"]}\nالكمية: {r["quantity"]:,}\nالحالة: {r["order_status"]}\nالمبلغ: {r["sale_price"]:,.2f} ج' for r in rs]),reply_markup=main_kb())
async def cb(u,c):
 q=u.callback_query; d=q.data
 if d=='home': await q.message.reply_text('القائمة الرئيسية:',reply_markup=main_kb()); await q.answer(); return
 if d in ('socials','programs'):
  if d=='socials':
   kb=[]; row=[]
   for i,x in enumerate(SOCIAL):
    row.append(InlineKeyboardButton(x,callback_data=f'sc:{i}'))
    if len(row)==2:kb.append(row);row=[]
   if row:kb.append(row)
   kb.append([InlineKeyboardButton('🔙 الرئيسية',callback_data='home')]); await q.message.edit_text('📱 اختر المنصة:',reply_markup=InlineKeyboardMarkup(kb))
  else:
   ps=await programs(); cats={}
   for s in ps: cats[pcat(s.get('name') or s.get('title') or '')]=1
   kb=[[InlineKeyboardButton(k,callback_data=f'pc:{k}')] for k in cats]; kb.append([InlineKeyboardButton('🔙 الرئيسية',callback_data='home')]); await q.message.edit_text('💻 اختر القسم:',reply_markup=InlineKeyboardMarkup(kb))
  await q.answer(); return
 if d.startswith('sc:'): await social_list(q,c,SOCIAL[int(d.split(':')[1])].split(' ',1)[1]); return
 if d.startswith('s:'): await social_detail(q,c,d.split(':')[1]); return
 if d=='sorder': c.user_data['step']='link'; await q.message.reply_text('🔗 ابعت الرابط:'); await q.answer(); return
 if d.startswith('pc:'): await program_list(q,c,d[3:]); return
 if d.startswith('p:'): await program_detail(q,c,d.split(':',1)[1]); return
 if d=='porder': await ask_qty(q,c); return
 if d=='cancel': c.user_data.clear(); await q.message.reply_text('❌ تم إلغاء الطلب.',reply_markup=main_kb()); await q.answer(); return
 if d=='confirm':
  s=c.user_data['sel']; oid=save(q.from_user.id,q.from_user.username or '',s['provider'],s,c.user_data.get('link',''),c.user_data['q'],c.user_data['cost'],c.user_data['sale']); c.user_data['proof']=oid; c.user_data['step']=None
  await q.message.reply_text(f'💳 الدفع\n\nرقم الطلب: #{oid}\nالمبلغ: {Decimal(c.user_data["sale"]):,.2f} ج\n\nطريقة الدفع: {PAYMENT_METHOD}\nالاسم: {PAYMENT_NAME}\nالرقم: {PAYMENT_NUMBER or "راجع الإدارة"}\n\nبعد التحويل ابعت صورة إثبات الدفع هنا.'); await q.answer(); return
 if d.startswith('a:'):
  if q.from_user.id!=ADMIN_ID:return await q.answer('غير مسموح',show_alert=True)
  oid=int(d[2:]); x=db(); r=x.execute('SELECT * FROM orders WHERE id=?',(oid,)).fetchone(); x.close();
  res=await (alk_add(r['service_id'],r['link'],r['quantity']) if r['provider']=='alkabos' else xorder(r['service_id'],r['quantity'])); pid=(res.get('order') or res.get('order_id') or res.get('id')) if isinstance(res,dict) else None
  if isinstance(res,dict) and res.get('error'): await q.message.reply_text(f'❌ فشل التنفيذ: {res["error"]}'); return await q.answer()
  x=db(); x.execute("UPDATE orders SET payment_status='paid',order_status='submitted',provider_order_id=? WHERE id=?",(str(pid or ''),oid)); x.commit(); x.close(); await c.bot.send_message(r['user_id'],f'✅ تم اعتماد وتنفيذ طلبك #{oid}.'); await q.message.reply_text(f'✅ تم إرسال الطلب #{oid}.'); await q.answer(); return
 if d.startswith('r:'):
  if q.from_user.id!=ADMIN_ID:return await q.answer('غير مسموح',show_alert=True)
  oid=int(d[2:]); x=db(); r=x.execute('SELECT user_id FROM orders WHERE id=?',(oid,)).fetchone(); x.execute("UPDATE orders SET payment_status='rejected',order_status='rejected' WHERE id=?",(oid,)); x.commit(); x.close(); await c.bot.send_message(r['user_id'],f'❌ تم رفض إثبات الدفع للطلب #{oid}.'); await q.answer('تم الرفض'); return
 await q.answer()
async def balance(u,c):
 if u.effective_user.id==ADMIN_ID: await u.message.reply_text(str(await alk_balance()))
async def catalog(u,c):
 if u.effective_user.id!=ADMIN_ID:return
 ss=await socials(); rate=await fx(); out=[f'📋 الخدمات: {len(ss)}','USD/EGP: '+str(rate),'']
 for s in sorted(ss,key=lambda x:int(str(x.get('service','0'))) if str(x.get('service','0')).isdigit() else 999999):
  _,sale=price(s.get('rate','0'),1000,rate); out.append(f'🆔 {s.get("service")}\n📌 {s.get("name")}\n📂 {s.get("category")}\n🔢 {s.get("min")} - {s.get("max")}\n🛡️ {s.get("refill")}\n💰 {sale:,.2f} ج/1000\n')
 text='\n'.join(out)
 for i in range(0,len(text),3800): await u.message.reply_text(text[i:i+3800])
def main():
 if not BOT_TOKEN or not ALKABOS_API_KEY or not ADMIN_ID: raise RuntimeError('Missing BOT_TOKEN / ALKABOS_API_KEY / ADMIN_ID')
 init_db(); app=Application.builder().token(BOT_TOKEN).build(); app.add_handler(CommandHandler('start',start)); app.add_handler(CommandHandler('balance',balance)); app.add_handler(CommandHandler('catalog',catalog)); app.add_handler(CallbackQueryHandler(cb)); app.add_handler(MessageHandler(filters.PHOTO | (filters.TEXT & ~filters.COMMAND),text)); app.run_polling(allowed_updates=Update.ALL_TYPES)
if __name__=='__main__': main()
