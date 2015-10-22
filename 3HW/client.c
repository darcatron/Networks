/* Mathurshan Vimalesvaran */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <arpa/inet.h>
#include <sys/types.h> 
#include <sys/socket.h>
#include <sys/select.h>
#include <fcntl.h>
#include <netdb.h>
#include <netinet/in.h>

/* Global Constants */
#define BUFSIZE 514
#define TYPEWINDOWSEQSIZE 1
#define FILENAMESIZE 20
#define DATASIZE 512
#define REQSIZE 22 // (TYPEWINDOWSEQSIZE * 2) + FILENAMESIZE
#define DATAPKTSIZE 514 // (TYPEWINDOWSEQSIZE * 2) + DATASIZE

void error(const char *msg)
{
    perror(msg);
    exit(0);
}

typedef struct __attribute__((__packed__)) {
    // TODO: 
    // Q: does char need the byte size?
    // Q: cast from pointer to int of diff size warning 
    // Q: Network byte order??
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


int main(int argc, char *argv[])
{
    int sockfd, portno, n;
    int serverlen;
    struct sockaddr_in serveraddr;
    struct hostent *server;
    char *hostname;

    /* check command line arguments */
    if (argc != 3) {
       fprintf(stderr,"usage: %s <hostname> <port>\n", argv[0]);
       exit(0);
    }
    hostname = argv[1];
    portno = atoi(argv[2]);

    /* socket: create the socket */
    sockfd = socket(AF_INET, SOCK_DGRAM, 0);
    if (sockfd < 0) 
        error("ERROR opening socket");

    /* gethostbyname: get the server's DNS entry */
    server = gethostbyname(hostname);
    if (server == NULL) {
        fprintf(stderr,"ERROR, no such host as %s\n", hostname);
        exit(0);
    }

    /* build the server's Internet address */
    bzero((char *) &serveraddr, sizeof(serveraddr));
    serveraddr.sin_family = AF_INET;
    bcopy((char *)server->h_addr, 
      (char *)&serveraddr.sin_addr.s_addr, server->h_length);
    serveraddr.sin_port = htons(portno);

    // printf("Please enter the message: ");
    // bzero(buffer,256);
    // fgets(buffer,255,stdin);
    Request req;

    // sprintf(req.type, "%d", RRQ);
    req.type = RRQ;
    // sprintf(req.window_size, "%d", 2);
    req.window_size = 2;
    strcpy(req.filename, "test.txt");
    printf("req created => type: %d window_size: %d filename: %s\n", req.type, req.window_size, req.filename);

    /* send the message to the server */
    serverlen = sizeof(serveraddr);
    n = sendto(sockfd, (char *) &req, sizeof (Request), 0,
               (struct sockaddr *) &serveraddr, serverlen);
    if (n < 0) 
      error("ERROR in sendto");
    printf("req sent!\n");

    // bzero(buffer,256);
    // n = recvfrom(sockfd, buf, strlen(buf), 0, &serveraddr, &serverlen);
    // if (n < 0) 
    //   error("ERROR in recvfrom"); 

    close(sockfd);
    return 0;
}
