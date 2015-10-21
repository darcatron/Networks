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
#define TYPE_LEN 2
#define ID_LEN 20
#define LENGTH_LEN 4
#define MSG_ID_LEN 4
#define HEADER_LEN 50 // TYPE_LEN + (ID_LEN * 2) + LENGTH_LEN + MSG_ID_LEN
#define DATA_LEN 400
#define MAX_CLIENTS 20

void error(const char *msg)
{
    perror(msg);
    exit(0);
}

typedef struct __attribute__((__packed__)) {
    unsigned short msg_type;
    char source_id[ID_LEN];
    char dest_id[ID_LEN];
    unsigned int msg_len;
    unsigned int msg_id;
} Header;


int main(int argc, char *argv[])
{
    int sockfd, portno, n;
    struct sockaddr_in serv_addr;
    struct hostent *server;

    char buffer[256];
    if (argc < 3) {
       fprintf(stderr,"usage %s hostname port\n", argv[0]);
       exit(0);
    }
    portno = atoi(argv[2]);
    sockfd = socket(AF_INET, SOCK_STREAM, 0);
    if (sockfd < 0) 
        error("ERROR opening socket");
    server = gethostbyname(argv[1]);
    if (server == NULL) {
        fprintf(stderr,"ERROR, no such host\n");
        exit(0);
    }
    bzero((char *) &serv_addr, sizeof(serv_addr));
    serv_addr.sin_family = AF_INET;
    bcopy((char *)server->h_addr, 
         (char *)&serv_addr.sin_addr.s_addr,
         server->h_length);
    serv_addr.sin_port = htons(portno);
    if (connect(sockfd,(struct sockaddr *) &serv_addr,sizeof(serv_addr)) < 0) 
        error("ERROR connecting");
    // printf("Please enter the message: ");
    // bzero(buffer,256);
    // fgets(buffer,255,stdin);
    // TODO: send hello
    Header *to_send = malloc(sizeof (Header));
    to_send->msg_type = htons(1);
    strcpy(to_send->source_id, "test");
    strcpy(to_send->dest_id, "Server");
    to_send->msg_len = htonl(0);
    to_send->msg_id = htonl(0);
    n = write(sockfd, (char *) to_send, HEADER_LEN);
    if (n < 0) 
         error("ERROR writing to socket");
    bzero(buffer,256);
    n = read(sockfd,buffer,256);
    if (n < 0) 
         error("ERROR reading from socket");
    printf("p1: %s\n",buffer);
    
    strcpy(to_send->source_id, "test2");
    n = write(sockfd, (char *) to_send, HEADER_LEN);
    n = read(sockfd,buffer,256);
    printf("p2: %s\n",buffer);

    to_send->msg_type = htons(5);
    strcpy(to_send->dest_id, "test");
    n = write(sockfd, (char *) to_send, HEADER_LEN);
    write(sockfd, "HELLOOOOO", 9);
    n = read(sockfd,buffer,256);
    printf("chat: %s\n",buffer);
    // strcpy(to_send->source_id, "test");
    // strcpy(to_send->dest_id, "Server");
    // to_send->msg_len = htonl(0);
    // to_send->msg_id = htonl(0);
    n = write(sockfd, (char *) to_send, HEADER_LEN);
    while(1) {};
    close(sockfd);
    return 0;
}
