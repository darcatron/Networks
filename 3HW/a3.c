/* 
 * a3.c 
 * usage: a3 <port>
 * By: Mathurshan Vimalesvaran
 */

#include <stdio.h>
#include <unistd.h>
#include <stdlib.h>
#include <string.h>
#include <netdb.h>
#include <sys/types.h> 
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>

#define BUFSIZE 514
#define TYPEWINDOWSEQSIZE 1
#define FILENAMESIZE 20
#define DATASIZE 512
#define REQSIZE 22 // (TYPEWINDOWSEQSIZE * 2) + FILENAMESIZE
#define DATAPKTSIZE 514 // (TYPEWINDOWSEQSIZE * 2) + DATASIZE
#define MAX_TIMEOUTS 5
#define TIMEOUT_USEC 3000

typedef struct __attribute__((__packed__)) {
    char type;
    char window_size;
    char filename[FILENAMESIZE];
} Request;

typedef struct __attribute__((__packed__)) {
    char type;
    char seq_num;
    char data[DATASIZE];
} DataPkt;

enum types {
    RRQ = 1,
    DATA = 2,
    ACK = 3,
    ERROR = 4
};


/*
 * error - wrapper for perror
 */
void error(char *msg) {
  perror(msg);
  exit(1);
}

/*
 * Opens file and returns file pointer
 */
FILE* open_file(char* filename) {
  FILE *fp;
  fp = fopen(filename, "r");

  return fp;
}

/*
 * Returns file size
 */
int get_filesize(FILE *fp) {
  fseek(fp, 0, SEEK_END);
  int file_size = ftell(fp);
  fseek(fp, 0, SEEK_SET);
  
  return file_size;
}

/*
 * Sends packets up to and including window_max
 * Returns last sent packet
 */
int send_pkts(FILE *fp, int last_sent, int window_max, int sockfd, int* clientlen, struct sockaddr_in* clientaddr) {
  int final_seq_num = (get_filesize(fp) / DATASIZE); // this accounts for 0 byte DataPkt for file_size % 512 == 0
  int final_pkt_size = (get_filesize(fp) % DATASIZE);

  while (last_sent != window_max) {
    int n;
    DataPkt pkt;

    pkt.type = DATA;
    pkt.seq_num = ++last_sent;
    bzero(pkt.data, DATASIZE);
    int read_size = (pkt.seq_num == final_seq_num) ? final_pkt_size : DATASIZE;
    int r = fread(pkt.data, 1, read_size, fp);
    int send_size = (pkt.seq_num == final_seq_num) ? ((TYPEWINDOWSEQSIZE * 2) + final_pkt_size) : sizeof(DataPkt);
    n = sendto(sockfd, (char *) &pkt, send_size, 0, 
               (struct sockaddr *) clientaddr, *clientlen);
    if (n < 0) 
      error("ERROR in sendto");
  }
  return last_sent;
}

void send_err(int sockfd, int* clientlen, struct sockaddr_in* clientaddr) {
  int n;
  DataPkt pkt;

  pkt.type = ERROR;
  n = sendto(sockfd, (char *) &pkt, sizeof (DataPkt), 0, 
             (struct sockaddr *) clientaddr, *clientlen);
  if (n < 0)
    error("ERROR in sendto");
}

void send_file(int sockfd, int* clientlen, struct sockaddr_in* clientaddr, Request* req) {
  int last_sent = -1;
  FILE *fp = open_file(req->filename);
  int final_seq_num = (get_filesize(fp) / DATASIZE); // this accounts for 0 byte DataPkt for file_size % 512 == 0
  int window_min = 0;
  // window_max can't be greater than final_seq_num
  int window_max = (req->window_size - 1 > final_seq_num) ? final_seq_num : (req->window_size - 1);
  int num_timeouts = 0;
  int n;
  fd_set read_set;
  struct timeval timeout;
  
  last_sent = send_pkts(fp, last_sent, window_max, sockfd, clientlen, clientaddr);

  while (1) {
    DataPkt ack;
    bzero(ack.data, DATASIZE);
    FD_ZERO(&read_set);
    timeout.tv_sec = 0;
    timeout.tv_usec = TIMEOUT_USEC;
    FD_SET(sockfd, &read_set);
    n = select(sockfd + 1, &read_set, NULL, NULL, &timeout);

    if (n == 0) { // timed out
      num_timeouts++;

      if (num_timeouts == MAX_TIMEOUTS) {
        return -1; // stop communication
      }
      last_sent = send_pkts(fp, window_min - 1, window_max, sockfd, clientlen, clientaddr);
    }
    else {
      n = recvfrom(sockfd, (char *) &ack, (TYPEWINDOWSEQSIZE * 2), 0,
         (struct sockaddr *) clientaddr, clientlen);
      if (n < 0)
        error("ERROR in recvfrom");
      if (ack.seq_num >= window_min) { // ACK is new
        if (ack.seq_num == final_seq_num) {
          return 0; // completed
        }

        // adjust window accordingly
        window_min = ack.seq_num + 1;
        window_max = (window_min + (req->window_size - 1) > final_seq_num) ? final_seq_num : (window_min + (req->window_size - 1));
        last_sent = send_pkts(fp, last_sent, window_max, sockfd, clientlen, clientaddr);
      }
    }
  }
}

int main(int argc, char **argv) {
  int sockfd; /* socket */
  int portno; /* port to listen on */
  int clientlen; /* byte size of client's address */
  struct sockaddr_in serveraddr; /* server's addr */
  struct sockaddr_in clientaddr; /* client addr */
  struct hostent *hostp; /* client host info */
  char buf[BUFSIZE]; /* message buf */
  char *hostaddrp; /* dotted decimal host addr string */
  int optval; /* flag value for setsockopt */
  int n; /* message byte size */

  /* 
   * check command line arguments 
   */
  if (argc != 2) {
    fprintf(stderr, "usage: %s <port>\n", argv[0]);
    exit(1);
  }
  portno = atoi(argv[1]);

  /* 
   * socket: create the parent socket 
   */
  sockfd = socket(AF_INET, SOCK_DGRAM, 0);
  if (sockfd < 0) 
    error("ERROR opening socket");

  /* setsockopt: Handy debugging trick that lets 
   * us rerun the server immediately after we kill it; 
   * otherwise we have to wait about 20 secs. 
   * Eliminates "ERROR on binding: Address already in use" error. 
   */
  optval = 1;
  setsockopt(sockfd, SOL_SOCKET, SO_REUSEADDR, 
         (const void *)&optval , sizeof(int));

  /*
   * build the server's Internet address
   */
  bzero((char *) &serveraddr, sizeof(serveraddr));
  serveraddr.sin_family = AF_INET;
  serveraddr.sin_addr.s_addr = htonl(INADDR_ANY);
  serveraddr.sin_port = htons((unsigned short)portno);

  /* 
   * bind: associate the parent socket with a port 
   */
  if (bind(sockfd, (struct sockaddr *) &serveraddr, 
       sizeof(serveraddr)) < 0) 
    error("ERROR on binding");

  /* 
   * main loop: wait for a datagram, then echo it
   */
  clientlen = sizeof(clientaddr);
  while (1) {
    // recvfrom: receive a UDP datagram from a client
    Request *req = malloc(sizeof (Request));
    bzero(req->filename, FILENAMESIZE);
    n = recvfrom(sockfd, (char *) req, REQSIZE, 0,
         (struct sockaddr *) &clientaddr, &clientlen);
    if (n < 0)
      error("ERROR in recvfrom");

    if (access(req->filename, F_OK) == -1){
      send_err(sockfd, &clientlen, &clientaddr);
      free(req);
      continue;
    }

    int completed = 0, too_many_timeouts = -1;
    send_file(sockfd, &clientlen, &clientaddr, req); 
    free(req);
  }
}