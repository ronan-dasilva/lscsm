import numpy as np
from datetime import datetime
from pprint import pformat
from struct import pack, unpack
#from HSM import HSM
from os.path import isfile


def saveMat(mat,filename):
    """    
    Saves an array/matrix in binary format
    """    
    mat=np.reshape(np.array(mat),-1)
    with open(filename,'wb') as f:
        f.write(pack('<%dd'%len(mat),*mat))
        

def saveResults(lscsm,suppl_params,K=None,errors=None,corr=None,prefix='lscsmfit'): 
    """
    Saves lscsm fitting results and meta-parameters
    """
    
    filenames=[]
   
    # Save K (lscsm parameters)   
    #if not(K in [None,[]]):
    saveMat(K,prefix+'_K')
    filenames.append(prefix+'_K')
    
    # Save meta-parameters
    meta_params = dict(lscsm.get_param_values())
    suppl_params['stimsize']=lscsm.size
    suppl_params['date']=str(datetime.now().date())+'-'+str(datetime.now().time())[:8]
    with open(prefix+'_metaparams','w') as f:
        f.write('meta_params = {\n'+pformat(meta_params)[1:]+'\n\n')
        f.write('suppl_params = {\n'+pformat(suppl_params)[1:]+'\n\n')
    filenames.append(prefix+'_metaparams')
    
    # Save successive values of training and validation error
    if not (errors in [None,[],[None,None],[[],[]]]):
        assert len(errors)==2
        saveMat(errors,prefix+'_error')
        filenames.append(prefix+'_error')
    
    # Save successive values of training and validation correlation    
    if not (corr in [None,[],[None,None],[[],[]]]):
        assert len(corr)==2
        saveMat(corr,prefix+'_corr')
        filenames.append(prefix+'_corr')
        
    return filenames         


def loadVec(filename):
    """
    Load an array/matrix stored in binary format
    """     
    with open(filename,'rb') as f:
        binary=f.read()
    assert len(binary)%8==0
    return np.array(unpack('<%dd'%(len(binary)/8),binary))
    
    
def loadParams(filename):
    """
    Load meta-parameters
    """    
    with open(filename,'r') as f:
        exec(f.read())
    return meta_params,suppl_params
    

def loadErrCorr(filename):
    """
    Load successive values of training and validation error/correlation
    """
    vec=loadVec(filename)
    assert len(vec)%2==0
    return vec[:len(vec)/2], vec[len(vec)/2:]
    
    
def restoreLSCSM(checkpointname,training_inputs,training_set,update_mp={}):
    """
    Reloads meta-parameters of a checkpointed fit, updates some of them using update_mp, then uses them and the provided data to recreate a lscsm object
    Also loads and returns the associated parameter vector K and the suppl_params dictionary (supplementary parameters used for fitting, or in fact can contain any information one wants to store)  
    """
    # Load and update meta-parameters, use them to recreate the lscsm object
    meta_params, suppl_params = loadParams(checkpointname+'_metaparams')
    meta_params.update(update_mp)
    lscsm=LSCSM(training_inputs,training_set,**meta_params) 
    
    # Load K (return None if file not found)
    if isfile(checkpointname+'_K'):
        K=loadVec(checkpointname+'_K')
        if not(all([update_mp.keys()[i] in ['error_function', 'name'] for i in range(len(update_mp.keys()))])):
            print ('WARNING: Updating of meta-parameters might have changed model structure: the reloaded parameter vector (K) might not be compatible with it')
    else:
        K=None
        print ('WARNING:Parameter vector (K) file not found')
    
    return lscsm, K, suppl_params