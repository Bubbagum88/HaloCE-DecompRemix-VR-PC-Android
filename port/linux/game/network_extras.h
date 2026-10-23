#ifndef __NETWORK_EXTRAS_H
#define __NETWORK_EXTRAS_H

/* network.community_extras: the shared Armor choices and votes to kick or
ban (network_extras.c); FALSE: none sent, none read */
boolean network_extras_enabled(void);

/* Test73: the kinds after map sharing (OpenCE 232's text chat, 87-89,
OpenCE 244's aim assist policy, 90, and the extras, 91-94), which Test67-72
builds sent with other meanings */
boolean network_extras_kind(byte type);
/* a message received (machine_index the sender's on the host, NONE on a
client): FALSE when it is one of those kinds from a machine found to run a
Test67-72 build, or the message that shows it does (a host of network 29 or
before sending a kind past 89, or its vote's details as 88; a client sending
a kind the wrong way): not to be read */
boolean network_extras_receive(long machine_index, word const *message, word size);
/* whether a message of the kind is not to go to the machine (NONE: the
host): a Test67-72 build, or for the extras any host of network 29 or before */
boolean network_extras_blocked(long machine_index, byte type);
/* the host: whether any client runs a Test67-72 build */
boolean network_extras_old_clients(void);
/* each frame, in the lobby and in game (main.c): what is known of machines
that left, or of a host this machine no longer plays with, forgotten */
void network_extras_update(void);

#endif
