#ifndef MCC_OFFLINE_H
#define MCC_OFFLINE_H
/* This port (HaloCE Quest VR / Android) plays GulchCE's Halo 1 MCC maps solo
 * only. GulchCE carries MCC games online in its own network version 42 (a
 * SHA-256 in the game advertisement and messages 87-90); this port hosts and
 * joins OpenCE network 28 unchanged, so an MCC map is never hosted or joined:
 * the MCC loader refuses one in a network game (mcc_identity_loaded) and the
 * host's map lists do not offer them. The MCC host-only sends compile to
 * nothing; they are reached only by an MCC map hosted online. */
#define MCC_DISTRIBUTED_SEND(...) ((void)0)
#endif
