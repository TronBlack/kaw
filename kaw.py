#!/usr/bin/python3

import random
import os
import subprocess
import json #Make sure it is simplejson - Needed to parse Decimal("####.########")
import logging
import time

from decimal import Decimal
import decimal

#Set this to your raven-cli program
cli = "raven-cli"

#mode = "-testnet"
mode = ""
rpc_port = 8766
#Set this information in your raven.conf file (in datadir, not testnet3)
rpc_user = 'rpcuser'
rpc_pass = 'rpcpass555'

pin = False

## CONSTANTS
MSG_TYPE_METADATA = 0
MSG_TYPE_ASSET_MEMO = 2

def get_rpc_connection():
    from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException
    connection = "http://%s:%s@127.0.0.1:%s"%(rpc_user, rpc_pass, rpc_port)
    rpc_conn = AuthServiceProxy(connection, timeout=480)
    return(rpc_conn)

rpc_connection = get_rpc_connection()

def rpc_call(params):
    process = subprocess.Popen([cli, mode, params], stdout=subprocess.PIPE)
    out, err = process.communicate(timeout=None)
    process.stdout.close()
    process.stderr.close()
    return(out)

def get_blockinfo(num):
    hash = rpc_connection.getblockhash(num)
    blockinfo = rpc_connection.getblock(hash)
    return(blockinfo)

def get_block(hash):
    blockinfo = rpc_connection.getblock(hash)
    return(blockinfo)

def get_rawtx(tx):
    #print("Rawtx: " + tx)
    txinfo = rpc_connection.getrawtransaction(tx)
    return(txinfo)

def get_bci():
    bci = rpc_connection.getblockchaininfo()
    return(bci)

def decode_rawtx(txdata):
    #logging.debug("decoding: " + txdata)
    txjson = rpc_connection.decoderawtransaction(txdata)
    return(txjson)    

def decode_script(script):
    scriptinfo = rpc_connection.decodescript(script)
    return(scriptinfo)   

def ipfs_add(file):
    logging.info("Adding to IPFS")
    import ipfsapi
    api = ipfsapi.connect('127.0.0.1', 5001)
    res = api.add(file)
    logging.info(res)
    return(res['Hash'])

def ipfs_get(hash):    
    import ipfsapi
    api = ipfsapi.connect('127.0.0.1', 5001)
    res = api.get(hash)
    return()

def ipfs_pin_add(hash):
    import ipfsapi
    api = ipfsapi.connect('127.0.0.1', 5001)
    res = api.pin_add(hash)
    return(res)




##  DATABASE ACCESS #####################################################

import pymysql

class DB:

    def __init__(self):
        self.dbc = self.open_db()

    def open_db(self):
        self.db = pymysql.connect("localhost","root","abesec","kaw" )
        cursor = self.db.cursor()
        return(cursor)
   
    def get_db_version(self):
        self.dbc.execute("SELECT VERSION()")
        data =  self.dbc.fetchone()
        return("Database version : %s " % data)

    def commit(self):
        self.db.commit()

    def close_db(self):
        self.db.close()

    def get_last_block_id(self):
        sql = "SELECT MAX(block_id) as block_id from blocks"
        self.dbc.execute(sql)
        block_id = self.dbc.fetchone()[0]
        return(block_id)


    ## KAW - Specific ################################
    def create_tables():
        with open ("kaw.sql", "r") as myfile:
            sql=myfile.readlines()
        self.dbc.execute(sql)
        self.db.commit()


    def add_block(self, block_id, time, block_hash):
        sql = "INSERT INTO blocks(block_id, time, block_hash) VALUES (%d, %d, '%s')" % (block_id, time, block_hash)
        logging.debug(sql)
        try:
            self.dbc.execute(sql)
        except pymysql.err.IntegrityError as err:
            logging.error("Could not add block (Integrity Error): " + str(block_id))
            return(-1)
        except Exception as err:
            logging.critical(type(err))
            logging.critical(err)

        self.dbc.execute('SELECT MAX(block_id) as id FROM blocks')
        id = self.dbc.fetchone()[0]
        return(self.get_last_block_id())



    def add_tx(self, block_id, tx_hash):
        sql = "INSERT INTO txs(block_id, tx_hash) VALUES ('%d', '%s')" % (block_id, tx_hash)
        logging.debug(sql)
        self.dbc.execute(sql)
        logging.debug("Added TX - lastrowid is " + str(self.dbc.lastrowid))
        return(self.dbc.lastrowid)



    def add_asset(self, tx_id, vout, asset, amount, units, reissuable):
        sql = "INSERT INTO assets(tx_id, vout, asset, amount, units, reissuable) VALUES ('%d', '%d', '%s', '%f', '%d', '%d')" % (tx_id, vout, asset, amount, units, reissuable)
        logging.info(sql)
        self.dbc.execute(sql)
        return(self.dbc.lastrowid)
        
          

    def lookup_asset_id(self, asset):
        sql = "SELECT asset_id FROM assets WHERE asset='%s'" % (asset)
        logging.debug(sql)
        self.dbc.execute(sql)
        try:
            id = self.dbc.fetchone()[0]
        except:
            logging.critical("Looking up asset: " + asset)
            id = -1 #Not found
        return(id)

    def lookup_tx_hash(self, tx_hash):
        sql = "SELECT tx_id FROM txs WHERE tx_hash='%s'" % (tx_hash)
        self.dbc.execute(sql)
        #try:
        rslt = self.dbc.fetchone()
        tx_id = -1 if rslt == None else rslt[0]
        #except:
        #    tx_id = -1
        return(tx_id)


    def get_id(self, results):
        for row in results:
            id = row[0]
        return(id)        

    def add_vout(self, tx_id, vout, address, asset_id, sats):
        sql = "INSERT INTO vouts(tx_id, vout, address, asset_id, sats) VALUES ('%d', '%d', '%s', '%d', '%d')" % (tx_id, vout, address, asset_id, sats)
        #logging.debug(sql)
        #print(sql)
        self.dbc.execute(sql)
        return(self.dbc.lastrowid)

    def add_msg(self, tx_id, vout, asset_id, msg_type, ipfs, msg):
        sql = "INSERT INTO msgs(tx_id, vout, asset_id, msg_type, ipfs, msg) VALUES ('%d', '%d', '%d', '%d', '%d', '%s')" % (tx_id, vout, asset_id, msg_type, ipfs, msg)
        logging.info(sql)
        #print(sql)
        self.dbc.execute(sql)
        return(self.dbc.lastrowid)   

    def remove_msgs(self, tx_id):
        sql = "DELETE FROM msgs WHERE tx_id=('%d')" % tx_id;
        self.dbc.execute(sql)

    def remove_assets(self, tx_id):
        sql = "DELETE FROM assets WHERE tx_id=('%d')" % tx_id;
        self.dbc.execute(sql)

    def remove_vouts(self, tx_id):
        sql = "DELETE FROM vouts WHERE tx_id=('%d')" % tx_id;
        self.dbc.execute(sql)

    def remove_tx(self, tx_id):
        sql = "DELETE FROM txs WHERE tx_id=('%d')" % tx_id;
        self.dbc.execute(sql)

    def remove_block(self, block_id):
        sql = "DELETE FROM blocks WHERE block_id=('%d')" % block_id;
        self.dbc.execute(sql)        


        ## END KAW - Specific #################################################



## END DATABASE ACCESS #############################################

def asset_handler(dbc, asset_type, tx_id, vout, asset_script):
    asset_name = asset_script.get('asset_name')

    if (asset_name == 'RAVENCOINCASH') or (asset_name == 'WWW.RVNASSETSFORSALE.COM'):  # Too much processing overhead (abused)
        return(0)
    
    logging.debug("Type: " + asset_type)
    logging.debug("Asset: " + asset_name)


    asset_id = -1
    #asset_type = asset_script.get('type')

    if (asset_type == 'new_asset') or (asset_type == 'reissue_asset'):
        reissuable = 0 if asset_script.get('reissuable') == None else 1
        logging.debug("Reissuable: " + str(reissuable))

        logging.info(asset_script)
        logging.info(asset_script.get('units'))
        units = 0 if (asset_script.get('units') == None) else int(asset_script.get('units'))
        logging.info("Units: " + str(units))

        asset_id = dbc.add_asset(tx_id, vout, asset_script.get('asset_name'), asset_script.get('amount'), units, reissuable)
        if asset_script.get('hasIPFS') == True:
            asset_id = dbc.lookup_asset_id(asset_script.get('asset_name'))
            logging.info("Adding meta-data for: " + asset_script.get('asset_name'))
            add_msg(dbc, tx_id, vout, asset_id, MSG_TYPE_METADATA, asset_script.get('ipfs_hash') if asset_type == 'new_asset' else asset_script.get('new_ipfs_hash'))

    elif (asset_type == 'transfer_asset'):
        asset_msg = asset_script.get('asset').get('message')
        logging.info("Found transfer_asset")
        logging.info("get-asset: " + str(asset_script.get('asset')))
        logging.info("get-message: " + str(asset_script.get('asset').get('message')))
        logging.info("asset_msg: " + str(asset_msg))
        logging.info("asset_name: " + asset_name)
        if (asset_name == 'CATE'):
            exit()

        if asset_msg != None:
            asset_id = dbc.lookup_asset_id(asset_name)
            logging.info("Adding memo for: " + asset_name)
            add_msg(dbc, tx_id, vout, asset_id, MSG_TYPE_ASSET_MEMO, asset_msg)
            exit()


    return(asset_id)

# def determine_msg_type(asset_type, asset_script):
#     ipfs = 1
#     msg_type = 0

#     type = asset_script.get('type')
#     if asset_script.get('hasIPFS') == True:
#         if asset_script.get('hasIPFS') == True:
#             if (type == 'new_asset'):
#                 msg = asset_script.get('ipfs_hash')
#             else:
#                 msg = asset_script.get('new_ipfs_hash')
#             logging.info('Msg: ' + msg)


#         return(msg_type, ipfs, msg)
        
#     else:
#         return(-1, -1, '') # No message


# Add a msg
# There are 4 msg_types:
# 0 - Meta-data - used on asset issuance or re-issuance
# 1 - Messages - used when admin token sends from/to same address - signal for broadcast
# 2 - Memos (asset) - used with any transaction
# 3 - Memos (RVN) - used with any RVN transaction

# ipfs is 1 for ipfs encoding or 0 for hex encoding
def add_msg(dbc, tx_id, vout, asset_id, msg_type, msg):
    ipfs = 1 if msg[0] == 'Q' else 0  #Check for 'Qm....' for ipfs
    dbc.add_msg(tx_id, vout, asset_id, msg_type, ipfs, msg)
    if pin and ipfs:
        ipfs_pin_add(msg)


#Only add vouts that deal with assets, ignore others
def add_vouts(dbc, block_id, tx_id, vouts):
    vnum = 0
    for vout in vouts:
        #logging.info("vout: " + str(vout.get('value')))
        #logging.info(vout.get('scriptPubKey').get('asm'))
        asset_id = 0
        sats = 0
        address = ''
        asset_type = 'unset'
        #get_bci()
        #logging.debug("Script: " + vout.get('scriptPubKey').get('hex'))
        

        try:
            script = decode_script(vout.get('scriptPubKey').get('hex'))
            #logging.debug("VOUT " + str(vnum) + " script:" + vout.get('scriptPubKey').get('hex'))
            #logging.debug(script)
            asset_type = script.get('type')
            #logging.debug("Script: " + str(script))

        except UnicodeDecodeError:  #Handles a rare error in decoding
            print("Could not decode script in tx - utf-8 error.")




        ## This is here just to learn about new asset_types
        #if (asset_type != 'new_asset') and (asset_type != 'reissue_asset') and (asset_type != 'transfer_asset') and (asset_type != 'scripthash') and (asset_type != 'pubkeyhash') and (asset_type != 'pubkey') and (asset_type != 'nulldata') and (asset_type != 'nullassetdata') and (asset_type != 'unset') and (asset_type != 'witness_v0_keyhash'):
        #    logging.critical("New asset type: " + asset_type)
        #    exit()
        ###################################################        
        
        if (asset_type == 'transfer_asset') or (asset_type == 'new_asset') or (asset_type == 'reissue_asset'):
            logging.debug("ASSET TYPE FOUND")
            asset_id = asset_handler(dbc, asset_type, tx_id, vnum, script)
            #asset_amount = script.get('asset').get('amount')
            #logging.debug(script.get('asset'))
            #address =  script.get('addresses')[0]
            #if (address == ''):
            #    logging.critical("Address Not Found")            
            #dbc.add_vout(tx_id, vnum, address, asset_id, sats)
        else:
            # TODO TB20200618 - Need to find memos for RVN transactions after hard-fork of Feb 7, 2020
            #logging.info("Type: " + asset_type)
            if (block_id >= 1092672):
                logging.debug("Should be indexing memos for RVN transactions in add_vouts")

        vnum = vnum + 1

def add_txs(dbc, block_id, txs):
    #logging.info(txs)
    for tx in txs:
        tx_info = get_rawtx(tx)
        logging.debug("txinfo: " + tx_info)
        tx_detail = decode_rawtx(tx_info)
        tx_hash = tx_detail.get('hash')
        tx_id = dbc.add_tx(block_id, tx_hash)
        logging.info("Added tx_hash: " + tx_hash)
        add_vouts(dbc, block_id, tx_id, tx_detail.get('vout'))
        #logging.info("txdecoded: " + tx_detail.get('vout'))

#Remove tx and associated msgs, assets, vouts
def reset_tx(db, tx):
    tx_info = get_rawtx(tx)
    tx_hash = decode_rawtx(tx_info).get('hash')
    logging.info('Removing: tx_hash: ' + tx_hash)
    tx_id = db.lookup_tx_hash(tx_hash)
    logging.info('Removing: tx_id is ' + str(tx_id))
    if (tx_id > 0):
        db.remove_msgs(tx_id)
        db.remove_assets(tx_id)
        db.remove_vouts(tx_id)
        db.remove_tx(tx_id)

#Loop through txs, remove msgs, assets, vouts
def reset_txs(db, txs):
    for tx in txs:
        reset_tx(db, tx)



#Loop through all tx, and remove all msgs, assets, vouts
def reset_block(db, block_id):
    dta = get_blockinfo(block_id)
    tx_in_block = get_block(dta.get('hash'))
    txs = tx_in_block.get('tx')
    reset_txs(db, txs)
    db.remove_block(block_id)
    db.commit()  #Commit to the database after each block is complete

def main():
    db = DB()
    logging.info(db.get_db_version())

    #Get the blockheight of the chain
    blockheight = get_bci().get('blocks')
    starting_block = max(435456, db.get_last_block_id() + 1)



    ## FOR DEBUGGING ##############
    starting_block = 1289219
    reset_block(db, starting_block)
    ###############################

    logging.info("Starting block: " + str(starting_block))    


    for block_id in range(starting_block,blockheight):
        dta = get_blockinfo(block_id)
        logging.info("Block #" + str(block_id) + " - " + dta.get('hash'))
        logging.debug(dta.get('time'))

        logging.debug("Adding block to db")
        id = db.add_block(block_id, int(dta.get('time')), dta.get('hash'))
        if (id > 0):
            logging.debug("Added block as id: " + str(id))
            tx_in_block = get_block(dta.get('hash'))

            txs = tx_in_block.get('tx')

            add_txs(db, block_id, txs)
        else:
            logging.error("Skipping block - already added block #: " + str(block_id))

        db.commit()  #Commit to the database after each block is complete

    db.close_db()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main()


def test():
    db = DB()
    db.add_msg()    
