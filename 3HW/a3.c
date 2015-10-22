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
    // TODO: 
    // Q: does char need the byte size?
    // Q: cast from pointer to int of diff size warning
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
 * Opens file and sets up pointer
 * Returns file size
 */
int open_file(FILE *fp, char* filename) {
  fp = fopen(filename, "r");
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
  while (last_sent != window_max) {
    int n;
    DataPkt pkt;

    pkt.type = DATA;
    pkt.seq_num = ++last_sent;
    fread(pkt.data, 1, DATASIZE, fp);
    // TODO: sizeof needs to specify that the data is less than 512 bytes for the final send
    // TODO: original code says clientlen isn't a pointer for sendto
    printf("sending pkt=> type: %d seq_num: %d\n", pkt.type, pkt.seq_num);
    n = sendto(sockfd, (char *) &pkt, sizeof (DataPkt), 0, 
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
  // TODO: original code says clientlen isn't a pointer for sendto
  n = sendto(sockfd, (char *) &pkt, sizeof (DataPkt), 0, 
             (struct sockaddr *) clientaddr, *clientlen);
  if (n < 0)
    error("ERROR in sendto");
}

int send_file(int sockfd, int* clientlen, struct sockaddr_in* clientaddr, Request* req) {  
  // int last_ack = -1;
  int last_sent = -1;
  FILE *fp;
  int final_seq_num = (open_file(fp, req->filename) / DATASIZE); // this accounts for 0 byte DataPkt for file_size % 512 == 0
  int window_min = 0;
  // window_max can't be greater than final_seq_num
  int window_max = (req->window_size - 1 > final_seq_num) ? final_seq_num : (req->window_size - 1);
  int num_timeouts = 0;
  int n;
  fd_set read_set;
  struct timeval timeout;
  timeout.tv_usec = TIMEOUT_USEC;
  
  last_sent = send_pkts(fp, last_sent, window_max, sockfd, clientlen, clientaddr);

  while (1) {
    DataPkt *ack = malloc(sizeof (DataPkt));
    // TODO: verify clientaddr and clientlen dont need &
    // n = recvfrom(sockfd, (char *) ack, (TYPEWINDOWSEQSIZE * 2), 0,
    //      (struct sockaddr *) clientaddr, clientlen);
    // TODO: add this after everything else is working bzero(buf, BUFSIZE);
    FD_ZERO(&read_set);
    FD_SET(sockfd, &read_set);
    n = select(sockfd + 1, &read_set, NULL, NULL, &timeout);
    if (n < 0)
      error("ERROR in recvfrom");

    if (n == 0) { // timed out
      printf("timed out\n");
      num_timeouts++;

      if (num_timeouts == MAX_TIMEOUTS) {
        return -1; // stop communication
      }
      last_sent = send_pkts(fp, last_sent, window_max, sockfd, clientlen, clientaddr);
    }

    if (ack->seq_num >= window_min) { // ACK is new
      printf("received ack of %d\n", ack->seq_num);
      if (ack->seq_num == final_seq_num) {
        printf("final ack received!\n");
        return 0; // completed
      }

      // adjust window accordingly
      window_min = ack->seq_num + 1;
      window_max = (window_min + (req->window_size - 1) > final_seq_num) ? final_seq_num : (window_min + (req->window_size - 1));
      printf("new window: [%d : %d]\n", window_min, window_max);
      last_sent = send_pkts(fp, last_sent, window_max, sockfd, clientlen, clientaddr);
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
    // TODO: add this after everything else is working bzero(buf, BUFSIZE);
    n = recvfrom(sockfd, (char *) req, REQSIZE, 0,
         (struct sockaddr *) &clientaddr, &clientlen);
    if (n < 0)
      error("ERROR in recvfrom");

    // TODO: (cleanup) can remove if and else since all first requests should be RRQ
    if (req->type == RRQ) {
        printf("recieved request for file %s\n", req->filename);
        if (access(req->filename, F_OK) == -1){
          printf("404 sending ERROR\n");
          send_err(sockfd, &clientlen, &clientaddr);
          free(req);
          continue;
        }
    } 
    else {
      fprintf(stderr, "ERR!! Type is not RRQ!!\n");
      exit(1);
    }

    int completed = 0, too_many_timeouts = -1;
    // TODO: (cleanup) can remove outcome since there is nothing I need to output for it
    //                 send_file can be void return type
    //                 ifs below can be removed
    int outcome = send_file(sockfd, &clientlen, &clientaddr, req); 
    
    if (outcome == completed) {
      // completed file transfer
      fprintf(stderr, "FILE TRANSFER COMPLETE!\n");
    }
    else if (outcome == too_many_timeouts) {
      // stop communication, assumes the client will not send anything more to us
      fprintf(stderr, "TOO MANY TIMEOUTS!\n");
    }
    else {
      fprintf(stderr, "ERR!! Outcome is not 0, 1, nor -1!\n");
      exit(1);
    }

    free(req);

    /* ORIGINAL CODE BELOW */    

    // /* 
    //  * gethostbyaddr: determine who sent the datagram
    //  */
    // hostp = gethostbyaddr((const char *)&clientaddr.sin_addr.s_addr, 
    //           sizeof(clientaddr.sin_addr.s_addr), AF_INET);
    // if (hostp == NULL)
    //   error("ERROR on gethostbyaddr");
    // hostaddrp = inet_ntoa(clientaddr.sin_addr);
    // if (hostaddrp == NULL)
    //   error("ERROR on inet_ntoa\n");
    // printf("server received datagram from %s (%s)\n", 
    //    hostp->h_name, hostaddrp);
    // printf("server received %d/%d bytes: %s\n", strlen(buf), n, buf);
    
    // /* 
    //  * sendto: echo the input back to the client 
    //  */
    // n = sendto(sockfd, buf, strlen(buf), 0, 
    //        (struct sockaddr *) &clientaddr, clientlen);
    // if (n < 0) 
    //   error("ERROR in sendto");
  }
}