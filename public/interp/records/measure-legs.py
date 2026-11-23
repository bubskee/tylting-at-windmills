"""Extract matched readouts for the archived 4B Leg Day replay, using public weights.
Run with torch, transformers, numpy and sklearn. Output is compact public figure data.
"""
import argparse, json, warnings
from pathlib import Path
import numpy as np
import torch
from sklearn.decomposition import FastICA, PCA
from sklearn.exceptions import ConvergenceWarning
from transformers import AutoConfig, AutoModelForCausalLM, AutoTokenizer

ap=argparse.ArgumentParser()
ap.add_argument('--out',type=Path,required=True)
args=ap.parse_args()
model_id='Qwen/Qwen3.5-4B'
rev='851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a'
torch.set_num_threads(5)
device='mps' if torch.backends.mps.is_available() else 'cpu'
cfg=AutoConfig.from_pretrained(model_id,revision=rev,local_files_only=True).get_text_config()
tok=AutoTokenizer.from_pretrained(model_id,revision=rev,local_files_only=True)
model=AutoModelForCausalLM.from_pretrained(model_id,revision=rev,config=cfg,local_files_only=True,dtype=torch.bfloat16,attn_implementation='eager').eval().requires_grad_(False).to(device)
net=model.base_model
print('Loaded pinned model',device,flush=True)
# Four independently worded clues per species. Evaluation wording is excluded.
clues={
 'spider':['hangs from a silk thread','traps flies in a web','wraps its prey in silk','weaves an orb between branches'],
 'bee':['stores nectar in a hive','feeds larvae in wax cells','returns pollen to a hive','dances to tell the hive about flowers'],
 'ant':['follows a pheromone trail','marches in columns to food','tends aphids for honeydew','builds a mound over its tunnels'],
 'dog':['brings a thrown ball back','barks at the front door','wags its tail at the leash','herds sheep for a shepherd'],
 'cat':['purrs on a warm lap','stalks a mouse at dusk','scratches a sisal post','kneads a blanket with its paws'],
 'cow':['chews cud in a dairy herd','wears a bell in the pasture','gives milk to a calf','lowers its horns at the gate'],
 'horse':['carries a rider over jumps','trots on iron shoes','whinnies in the stable','has a mane that a rider can braid'],
 'duck':['paddles with webbed feet','quacks on the lake','dabbles for food in a pond','leads its ducklings into water'],
 'chicken':['pecks grain in the coop','roosts on a perch at night','broods over eggs in a henhouse','clucks to its chicks'],
 'crab':['hides its claws under a rock','scuttles across a tidal pool','pinches with its front claws','sheds a hard shell on the seabed']}
count='The number of legs on the animal that '
name='The animal that '
def tokens(s):return tok(s,add_special_tokens=False).input_ids
six,eight=(tokens(s)[0] for s in ['6','8'])
def forward(clue,prefix=count,patch=None,gradient=False):
    suffix=' is ' if prefix==count else ' is the'
    prompt=prefix+clue+suffix
    ids=tokens(prompt); pre=tokens(prefix+clue)
    assert ids[:len(pre)]==pre
    pos=len(pre)-1
    state={}
    def block_hook(_,inputs,out):
        h=out[0] if isinstance(out,tuple) else out
        state['h']=h[0,pos].detach().clone()
        if patch is None and not gradient:return
        vector=state['h'] if patch is None else patch
        vector=vector.detach().requires_grad_(gradient)
        state['vector']=vector
        result=h.clone()
        result[0,pos]=vector
        return (result,*out[1:]) if isinstance(out,tuple) else result
    def neuron_hook(_,inputs):state['neurons']=inputs[0][0,pos].detach().float().cpu().numpy().copy()
    hooks=[net.layers[12].register_forward_hook(block_hook),net.layers[13].mlp.down_proj.register_forward_pre_hook(neuron_hook)]
    try:
        with torch.set_grad_enabled(gradient):
            hidden=net(input_ids=torch.tensor([ids],device=device),use_cache=False).last_hidden_state
            logits=model.get_output_embeddings()(hidden[:,-1])[0].float()
            if gradient:state['gradient']=torch.autograd.grad(logits[six]-logits[eight],state['vector'])[0].detach().float().cpu().numpy()
    finally:
        for h in hooks:h.remove()
    state.update(prompt=prompt,position=pos,token=tok.decode([ids[pos]]),id=ids[pos],answer=tok.decode([int(logits.argmax())]))
    return state
clean=forward('spins webs');donor=forward('makes honey',name);edited=forward('spins webs',patch=donor['h'])
print('Observed answers:',repr(clean['answer']),repr(edited['answer']),flush=True)
refs=[];states=[];units=[];grad=[];fitidx=[]
for animal,items in clues.items():
    for clue in items:
        fit=animal in ('spider','bee')
        row=forward(clue,gradient=fit)
        if fit:grad.append(row['gradient']);fitidx.append(len(refs))
        refs.append({'animal':animal,**{k:row[k] for k in ['prompt','position','token','id']}})
        states.append(row['h'].float().cpu().numpy());units.append(row['neurons'])
    print('Reference bank:',animal,flush=True)
X=np.asarray(states,dtype='float64');N=np.array(units);H=np.array([r['h'].float().cpu().numpy() for r in [clean,donor]])
Y=np.array([clean['neurons'],edited['neurons']])
def vec(values):return np.round(values,6).tolist()
def card(ref,pair,ids,unit,standardize=True):
    ref=np.array(ref).reshape(len(refs),-1)
    pair=np.array(pair).reshape(2,-1)
    spider=np.array([x['animal']=='spider' for x in refs]);bee=np.array([x['animal']=='bee' for x in refs])
    gaps=ref[bee].mean(0)-ref[spider].mean(0)
    if standardize:
        center=ref.mean(0)
        scale=np.where(gaps<0,-1,1)/np.maximum(ref.std(0),1e-12)
        ref=(ref-center)*scale;pair=(pair-center)*scale
    else:scale=np.ones_like(gaps)
    return {'ids':list(ids),'selected':int(np.abs(gaps*scale).argmax()),'unit':unit,'reference':vec(ref),'pair':vec(pair)}
pca=PCA(n_components=6,svd_solver='full').fit(X);z=pca.transform(X)
ica=FastICA(n_components=6,whiten='unit-variance',random_state=91,max_iter=2000,tol=1e-4)
with warnings.catch_warnings():
    warnings.simplefilter('error',ConvergenceWarning)
    S=ica.fit_transform(z)
components={'ica':card(S,ica.transform(pca.transform(H)),range(1,7),'reference SD'),
'pca':card(z,pca.transform(H),range(1,7),'reference SD')}
A=X[fitidx];C=A-A.mean(0)
def direction(k,d):
    v=d/np.linalg.norm(d)
    components[k]=card(X@v,H@v,[1],'reference SD')
direction('means',A[4:].mean(0)-A[:4].mean(0))
u=np.linalg.svd(C@np.asarray(grad).T,full_matrices=False)[0]
direction('ace',C.T@u[:,0])
gap=N[4:8].mean(0)-N[:4].mean(0)
inds=np.argsort(-np.abs(gap))[:6]
components['neurons']=card(N[:,inds],Y[:,inds],map(int,inds),'post-gate activation',False)
lens=[]
with torch.no_grad():
    for r in (clean,donor):
        logits=model.get_output_embeddings()(net.norm(r['h'])).float()
        ids=logits.topk(20).indices.tolist()
        lens.append([{'id':i,'token':tok.decode([i]),'logit':float(logits[i])} for i in ids])
out={'model':model_id,'revision':rev,'device':device,'dtype':'bfloat16','attention':'eager','layer':12,'hook':'decoder block output','neuron_hook':'block 13 MLP input to down_proj, post-gating','source':{k:clean[k] for k in ['prompt','position','id','token','answer']},'donor':{k:donor[k] for k in ['prompt','position','id','token']},'patched_answer':edited['answer'],'reference':refs,'components':components,'raw':lens,'fit':{'components':6,'seed':91,'ica_iterations':int(ica.n_iter_),'reference_count':len(refs),'gradient_target':'logit(6) minus logit(8) at the last prompt position','contrast':'four spider and four bee reference rows; clean replay wording excluded','selection':'Largest absolute standardized bee minus spider reference mean for ICA and PCA. Residual scores oriented toward the bee reference mean. Neurons ranked by absolute unscaled mean gap.'}}
args.out.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print('Saved',args.out,flush=True)
