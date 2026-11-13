#!/usr/bin/env python3
"""Distribution smoke tests: actual defaults, isolated checkout and production gates."""
import json, os, shutil, socket, subprocess, tempfile, time, urllib.request, urllib.error
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
KIND=(ROOT/'config/distribution').read_text().strip()
with tempfile.TemporaryDirectory(prefix='heartshop-standalone-') as temp:
    base=Path(temp);repo=base/'repo'
    shutil.copytree(ROOT,repo,ignore=shutil.ignore_patterns('.git','var','private','__pycache__'))
    with socket.socket() as sock:
        sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
    origin=f'http://localhost:{port}'
    log=(base/'server.log').open('w')
    proc=subprocess.Popen(['php','scripts/dev/start.php',str(port)],cwd=repo,stdout=log,stderr=log,start_new_session=True)
    def request(path,data=None,headers=None):
        hdr=dict(headers or {})
        if data is not None:
            data=json.dumps(data).encode();hdr.setdefault('Content-Type','application/json');hdr.setdefault('Origin',origin)
        req=urllib.request.Request(origin+path,data=data,headers=hdr)
        try:r=urllib.request.urlopen(req,timeout=5)
        except urllib.error.HTTPError as e:r=e
        with r:
            raw=r.read()
            return r.status, json.loads(raw) if 'application/json' in r.headers.get('Content-Type','') else raw,r.headers
    try:
        for _ in range(100):
            try:
                if request('/heartshop/')[0]==200:break
            except OSError:pass
            time.sleep(.05)
        else:raise AssertionError('Server failed: '+(base/'server.log').read_text())
        code,cfg,_=request('/heartshop/api/order.php');assert code==200
        assert len(cfg['offers'])==1 and cfg['sandbox'] is True
        typ='shipping' if KIND=='goods' else 'voucher'
        assert cfg['product']['type']==typ
        if KIND=='goods':assert cfg['invoice'] is True and cfg['delivery']['kurier']
        else:
            assert cfg['invoice'] is False and not cfg['delivery']
            assert not (repo/'public/heartshop/api/furgonetka.php').exists()
            assert request('/heartshop/api/furgonetka/orders')[0] in [403,404]
        for path in ['/heartshop/api/config.php','/scripts/dev/router.php','/var/local/.env','/heartshop/.htaccess']:
            assert request(path)[0] in [403,404],path
        assert request('/heartshop/',headers={'Host':'attacker.invalid'})[0]==403
        data={'qty':1,'name':'Test Buyer','email':'buyer@example.invalid','terms':True,'invoice':False}
        if KIND=='goods':data.update(phone='500600700',delivery='kurier',street='Test 1',postcode='00-001',city='Test')
        else:data.update(recipient='Ania')
        key={'Idempotency-Key':'a'*32}
        assert request('/heartshop/api/order.php',data,dict(key,Origin='http://attacker.invalid'))[0]==403
        wrong=dict(data,offer='masaz-60' if KIND=='goods' else 'magic-box')
        assert request('/heartshop/api/order.php',wrong,{'Idempotency-Key':'b'*32})[0]==422
        code,order,_=request('/heartshop/api/order.php',data,key);assert code==200,order
        assert request('/heartshop/api/order.php',data,key)[1]['orderId']==order['orderId']
        assert request('/__dev/settle',{'orderId':order['orderId']}, {'Origin':'http://attacker.invalid'})[0]==403
        assert request('/__dev/settle',{'orderId':order['orderId']})[1]['status']=='paid'
        status=request('/heartshop/api/status.php?o='+order['orderId'])[1]
        assert status['status']=='paid' and status['demo'] is True and status['testPayment'] is True and status['type']==typ
        if KIND=='vouchers':
            assert len(status['vouchers'])==1
            assert request('/heartshop/twoj-voucher.html?o='+order['orderId'])[0]==200
        else:
            assert request('/heartshop/api/furgonetka/orders',headers={'Authorization':'f'*32})[1]==[]
        code,_,h=request('/heartshop/api/panel.php?action=login',{'password':'local-heartshop-only'});assert code==200
        cookie=h['Set-Cookie'].split(';')[0]
        code,orders,_=request('/heartshop/api/panel.php?action=orders',headers={'Cookie':cookie});assert code==200 and len(orders['orders'])==1
        if KIND=='vouchers':
            code,_,_=request('/heartshop/api/panel.php?action=redeem',{'code':orders['orders'][0]['vouchers'][0]['code']},{'Cookie':cookie});assert code==200
        # Local simulator: a canceled payment resumes under the same order and can still be paid.
        retry={'Idempotency-Key':'5'*32}  # keys c-f, 7 and 9 belong to the production checks
        code,first,_=request('/heartshop/api/order.php',data,retry);assert code==200 and first['redirectUrl'],first
        assert request('/__dev/settle',{'orderId':first['orderId'],'cancel':True})[1]['status']=='canceled'
        code,again,_=request('/heartshop/api/order.php',data,retry)
        assert code==200 and again['orderId']==first['orderId'] and again['redirectUrl']==first['redirectUrl'],again
        assert request('/__dev/settle',{'orderId':first['orderId']})[1]['status']=='paid'
        assert request('/heartshop/api/status.php?o='+first['orderId'])[1]['status']=='paid'
        code,done,_=request('/heartshop/api/order.php',data,retry);assert code==200 and done=={'orderId':first['orderId'],'status':'paid'},done
        print('PASS local simulator: cancel, retry and pay keep one order')
        assert request('/__dev/paymove.js')[0]==200
        print('PASS actual '+KIND+' distribution: start, boundaries, order, idempotency, simulation, panel and fulfillment isolation')
    finally:
        import signal
        os.killpg(proc.pid,signal.SIGTERM);proc.wait(timeout=5);log.close()

    # Production mode: use only a stub provider, never the network. Copy and edit the
    # actual deployment config to test BOTH production_ready and per-offer demo gates.
    runtime=repo/'public/heartshop/api'
    env=repo/'var/local/.env';env.write_text(env.read_text().replace('PAYMOVE_ENV=sandbox','PAYMOVE_ENV=production').replace(origin,'https://shop.example.com'));env.chmod(0o600)
    runner=base/'production.php'
    runner.write_text('''<?php
$_SERVER['DOCUMENT_ROOT']=$argv[1].'/public';require $argv[1].'/public/heartshop/api/lib.php';
$input=['qty'=>1,'name'=>'Test Buyer','email'=>'buyer@example.invalid','recipient'=>'Ania','terms'=>true,'invoice'=>false,'phone'=>'500600700','delivery'=>'kurier','street'=>'Test 1','postcode'=>'00-001','city'=>'Test'];
$calls=0;$lost=($argv[3]??'')==='lost';$now=time()+(int)($argv[4]??0);
// 'lost': the create request never reaches PAYMOVE, leaving the order uncertain.
$provider=function($id)use(&$calls,$lost){$calls++;if($lost)throw new PaymoveFailure('network',0,7);return 'https://checkout.paymove.io/fixture/'.$id;};
try { $result=prepareCheckout($input,str_repeat($argv[2],32),$provider,$now);echo json_encode(['calls'=>$calls,'order'=>findOrder($result['orderId'])]); }
catch(CheckoutProblem $e){echo json_encode(['calls'=>$calls,'error'=>$e->reason,'orderId'=>$e->orderId]);}
''')
    penv=dict(os.environ,HEARTSHOP_ENV_FILE=str(env));penv.pop('HEARTSHOP_ORIGIN',None)
    def production(key,mode='',later=0):return json.loads(subprocess.check_output(['php',str(runner),str(repo),key,mode,str(later)],env=penv,stderr=subprocess.DEVNULL))
    p=runtime/'config.php';original=p.read_text()
    a=production('c');assert a['error']=='demo_only' and a['calls']==0
    p.write_text(original.replace("'production_ready' => false","'production_ready' => true"))
    a=production('d');assert a['error']=='demo_only' and a['calls']==0
    p.write_text(original.replace("'demo'    => true","'demo'    => false").replace("'demo'         => true","'demo'         => false"))
    a=production('e');assert a['error']=='demo_only' and a['calls']==0
    p.write_text(p.read_text().replace("'production_ready' => false","'production_ready' => true"))
    a=production('f');assert a['calls']==1 and a['order']['data']['snapshot']['demo'] is False and a['order']['data']['snapshot']['test_payment'] is False
    assert a['order']['offer_type']==typ
    print('PASS production gates: default denied, each independent gate denied, configured real offer accepted with stub provider')
    # A recovered retry re-checks the CURRENT gates before creating a payment.
    r=production('7','lost');assert r['error']=='payment_wait' and r['calls']==1
    lost_id=r['orderId'];ready=p.read_text()
    p.write_text(ready.replace("'production_ready' => true","'production_ready' => false"))
    r=production('7','',10);assert r['error']=='demo_only' and r['calls']==0 and r['orderId']==lost_id
    p.write_text(ready)
    # The stub link has no PAYMOVE hash, so the post-create status read holds it for review.
    r=production('7','',20);assert r['calls']==1 and r['orderId']==lost_id and r['error']=='payment_review',r
    print('PASS closing sales blocks a recovered create; reopening resumes the same order')

    # Complete the newly configured non-demo offer and exercise the real export endpoint.
    pay=base/'paid.php'
    pay.write_text("<?php $_SERVER['DOCUMENT_ROOT']=$argv[1].'/public';require $argv[1].'/public/heartshop/api/lib.php';$o=findOrder($argv[2]);applyPaymentEvent(['externalId'=>$o['external_id'],'orderId'=>'synthetic-provider-id','price'=>$o['total'],'status'=>'COMPLETED']);")
    subprocess.run(['php',str(pay),str(repo),a['order']['external_id']],env=penv,check=True)
    export=base/'export.php'
    export.write_text("<?php $_SERVER['DOCUMENT_ROOT']=$argv[1].'/public';$_SERVER['REQUEST_METHOD']='GET';$_SERVER['HTTP_AUTHORIZATION']=str_repeat('f',32);$_GET['route']='orders';require $argv[1].'/public/heartshop/api/furgonetka.php';")
    rows=json.loads(subprocess.check_output(['php',str(export),str(repo)],env=penv))
    assert len(rows)==1 and rows[0]['products'][0]['sourceProductId']=='magic-box'
    assert rows[0]['totalPaid']==65.99
    print('PASS Goods production-configured paid order exports to Furgonetka; earlier demo does not')
