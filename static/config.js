let CHAIN_ID;
let CHAIN_NAME;
let RPC_URL;
let RELAY_URL;

if(window.location.hostname == 'humanpow.bitpow.org'){
  RELAY_URL = "wss://humanpow.bitpow.org/relay";

}else{
  RELAY_URL = "ws://192.168.1.9:8030/relay";

}

CHAIN_ID = '0x1';
CHAIN_NAME = 'Ethereum Mainnet';
RPC_URL = "https://rpc.particle.network/evm-chain";


export {
  CHAIN_ID,
  CHAIN_NAME,
  RPC_URL,
  RELAY_URL,
}

// export default{
//     name: "default"
// }