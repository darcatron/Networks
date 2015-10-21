/* Mathurshan Vimalesvaran */
/* 
    ERROR NOTES:    There is an error with read() that I could not figure out.
                    If a client disconnects with or without sending EXIT, the 
                    read does not get the correct header from the client and 
                    therefore does not recognize what type was sent. Sometimes 
                    read() returns 0, other times it returns bad data in some
                    of the header fields. I could not determine the root of this
                    cause and was too late in asking in for help on the issue.
*/

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

static char *str_replace(char *orig, char *rep, char *with);

enum types {
    HELLO = 1,
    HELLO_ACK = 2,
    LIST_REQUEST = 3,
    CLIENT_LIST = 4,
    CHAT = 5,
    EXIT = 6,
    CLIENT_ALREADY_PRESENT = 7,
    CANNOT_DELIVER = 8
};

typedef struct __attribute__((__packed__)) {
    unsigned short msg_type;
    char source_id[ID_LEN];
    char dest_id[ID_LEN];
    unsigned int msg_len;
    unsigned int msg_id;
} Header;

typedef struct {
    char id[ID_LEN];
    int active;
    int fd;
} ClientInfo;

typedef struct { /* represents a pool of connected descriptors */
    int maxfd; /* largest descriptor in active_set */
    fd_set active_set; /* set of all active descriptors */
    fd_set write_set; /* subset of descriptors ready for writing */
    fd_set read_set; /* subset of descriptors ready for reading */
    int nready; /* number of ready descriptors from select */
    ClientInfo *clients[MAX_CLIENTS];
} Pool;

void error(const char *msg) {
    perror(msg);
    exit(1);
}

Header *parse_header(int fd) {
    int n;
    Header *data = malloc(sizeof (Header));

    n = read(fd, (char *) data, HEADER_LEN);
    if (n == 0) { return NULL; }

    data->msg_type = ntohs(data->msg_type);
    data->msg_len = ntohl(data->msg_len);
    data->msg_id = ntohl(data->msg_id);
    
    return data;
}

void send_response(Pool *pool, Header *original, int msg_type, int socket_fd) {
    Header *to_send = malloc(sizeof (Header));
    char data[DATA_LEN];

    switch (msg_type) {
        case HELLO_ACK : 
        {
            to_send->msg_type = htons(HELLO_ACK);
            strcpy(to_send->source_id, "Server");
            strcpy(to_send->dest_id, original->source_id);
            to_send->msg_len = htonl(0);
            to_send->msg_id = htonl(original->msg_id);
            break;
        }
        case CLIENT_LIST :
        {         
            to_send->msg_type = htons(CLIENT_LIST);
            strcpy(to_send->source_id, "Server");
            strcpy(to_send->dest_id, original->source_id);
            to_send->msg_id = htonl(original->msg_id);
            to_send->msg_len = htonl(create_list(pool, data, original->source_id));
            break;
        }
        case CLIENT_ALREADY_PRESENT :
        {
            to_send->msg_type = htons(CLIENT_ALREADY_PRESENT);
            strcpy(to_send->source_id, "Server");
            strcpy(to_send->dest_id, original->source_id);
            to_send->msg_len = htonl(0);
            to_send->msg_id = htonl(original->msg_id);
            break;
        }
        case CANNOT_DELIVER :
        {
            to_send->msg_type = htons(CANNOT_DELIVER);
            strcpy(to_send->source_id, "Server");
            strcpy(to_send->dest_id, original->source_id);
            to_send->msg_len = htonl(0);
            to_send->msg_id = htonl(original->msg_id);
        }
    }
    write(socket_fd, (char *) to_send, HEADER_LEN);
    if (ntohl(to_send->msg_len)) { write(socket_fd, data, ntohl(to_send->msg_len)); }
    free(to_send);
}

void send_chat(Header *to_send, int sender_fd, int receiver_fd) {
    // get chat msg
    char data[to_send->msg_len];
    bzero(data, to_send->msg_len);
    read(sender_fd, data, to_send->msg_len);

    // adjust header to send
    to_send->msg_type = htons(CHAT);
    to_send->msg_len = htonl(to_send->msg_len);
    to_send->msg_id = htonl(to_send->msg_id);

    // send chat msg
    write(receiver_fd, (char *) to_send, HEADER_LEN);
    write(receiver_fd, data, ntohl(to_send->msg_len));
}

/* Updates data with client list and returns length of list */
int create_list(Pool *pool, char *data, char *requester) {
    bzero(data, DATA_LEN);
    int client_num, total_len = 0, data_index = 0;

    for (client_num = 0; client_num < MAX_CLIENTS; ++client_num) {
        ClientInfo *client = pool->clients[client_num];
        
        if (client != NULL && client->active && strcmp(client->id, requester) != 0) {   
            total_len += strlen(client->id);

            int cur_char;
            for (cur_char = 0; cur_char < strlen(client->id); ++cur_char) {
                data[data_index] = client->id[cur_char];
                data_index++;
            }
            data[data_index++] = '\0';
        }
    }
    return total_len;
}

void init_pool(Pool *pool, int sockfd) {
    pool->maxfd = sockfd;
    FD_ZERO(&pool->active_set);
    FD_ZERO(&pool->write_set);
    FD_ZERO(&pool->read_set);
    pool->nready = 0;
    int i;
    for (i = 0; i < MAX_CLIENTS; ++i) { pool->clients[i] = NULL; }
    FD_SET(sockfd, &pool->active_set); // add descriptor to set
}

void remove_client(Pool *pool, ClientInfo *client) {
    FD_CLR(client->fd, &pool->active_set);
    close(client->fd);
    free(client);
    client = NULL;
}

void set_inactive(Pool *pool, ClientInfo *client) {
    client->active = 0;
    FD_CLR(client->fd, &pool->active_set);
    // TODO Q: is this needed?
    close(client->fd);
}

int max_fd(int serversocket, ClientInfo **clients_list) {
    int i, maxfd = serversocket;

    for (i = 0; i < MAX_CLIENTS; ++i)
    {
        if (clients_list[i] != NULL && clients_list[i]->fd > maxfd) {
            maxfd = clients_list[i]->fd;
        }
    }
    return maxfd;
}

// TODO: test all these
void check_clients(Pool *pool) {
    int client_num, fd;

    for (client_num = 0; client_num < MAX_CLIENTS; ++client_num) {
        ClientInfo *client = pool->clients[client_num];

        if (client != NULL && 
            FD_ISSET(client->fd, &pool->read_set)) {
            Header *header = parse_header(fd);
            if (header == NULL) {
                set_inactive(pool, client);
                free(header);
                continue;
            }
            // read types can only be LIST_REQUEST, CHAT, and EXIT
            if (strcmp(client->id, header->source_id) != 0) {
                // client id must be the same
                remove_client(pool, client);
            }
            else if (header->msg_type == LIST_REQUEST) {
                send_response(pool, header, CLIENT_LIST, fd);
            }
            else if (header->msg_type == CHAT) {
                int recipient = find_in_clients(pool, header->dest_id);
                
                if (header->dest_id == NULL ||
                    strlen(header->dest_id) == 0 ||
                    strcmp(header->source_id, header->dest_id) == 0) {
                    remove_client(pool, client);
                }
                else if (recipient != -1 && pool->clients[recipient]->active) {
                    // if client exists and client active
                    send_chat(header, fd, pool->clients[recipient]->fd);
                }
                else {
                    // discard msg
                    // TODO: test this 
                    // char data[header->msg_len];
                    // bzero(data, header->msg_len);
                    read(fd, NULL, header->msg_len);
                    send_response(pool, header, CANNOT_DELIVER, fd);
                }
            }
            else if (header->msg_type == EXIT) {
                remove_client(pool, client);
            }
            else {
                remove_client(pool, client);
            }
            free(header);
        }
    }
}

void add_client(int serversocket, int newsockfd, Pool *pool) {
    Header *header = parse_header(newsockfd);
    int i;

    if (header->msg_type == HELLO) {
        int client_index = find_in_clients(pool, header->source_id);

        if (client_index != -1) {
            // if client already exists
            ClientInfo *client = pool->clients[client_index];

            if (client->active) {
                send_response(pool, header, CLIENT_ALREADY_PRESENT, newsockfd);
                close(newsockfd);
            }
            else {
                // not active, set to active
                client->active = 1;
                // update fd
                client->fd = newsockfd;
                FD_SET(newsockfd, &pool->active_set);
                send_response(pool, header, HELLO_ACK, newsockfd);
                send_response(pool, header, CLIENT_LIST, newsockfd);
            }
            free(header);
        }
        else {
            // check if room
            int next_available = find_in_clients(pool, NULL);
            if (next_available == -1) {
                // max connections established
                close(newsockfd);
                free(header);
                return;
            }

            // save client info
            ClientInfo *new_client = malloc(sizeof (ClientInfo));
            strcpy(new_client->id, header->source_id);
            new_client->active = 1;
            new_client->fd = newsockfd;

            // update pool
            pool->clients[next_available] = new_client;
            pool->maxfd = max_fd(serversocket, pool->clients);
            FD_SET(newsockfd, &pool->active_set);

            send_response(pool, header, HELLO_ACK, newsockfd);
            send_response(pool, header, CLIENT_LIST, newsockfd);
            free(header);
            return; // prevent new socket from being closed
        }
    }
    close(newsockfd);
}

int find_in_clients(Pool *pool, char *name) {
    int i;
    if (name == NULL) {
        // find next available index
        for (i = 0; i < MAX_CLIENTS; ++i) {
            if (pool->clients[i] == NULL) {
                return i;
            }
        }
    }
    else {
        // find index of name
        for (i = 0; i < MAX_CLIENTS; ++i) {
            if (pool->clients[i] != NULL && 
                strcmp(pool->clients[i]->id, name) == 0) {
                return i;
            }
        }
    }

    return -1;
}

int main(int argc, char *argv[]) {
    // set up server socket
    int sockfd, newsockfd, portno, opts=1;
    socklen_t clilen;
    struct sockaddr_in serv_addr, cli_addr;
    int n;
    if (argc < 2) {
        fprintf(stderr,"ERROR, no port provided\n");
        exit(1);
    }
    
    sockfd = socket(AF_INET, SOCK_STREAM, 0);
    setsockopt(sockfd, SOL_SOCKET, SO_REUSEADDR, &opts, sizeof opts);
    if (sockfd < 0) 
        error("ERROR opening socket");
    
    bzero((char *) &serv_addr, sizeof(serv_addr));
    portno = atoi(argv[1]);
    serv_addr.sin_family = AF_INET;
    serv_addr.sin_addr.s_addr = INADDR_ANY;
    serv_addr.sin_port = htons(portno);

    if ((opts = fcntl(sockfd, F_GETFL)) < 0) {
        printf("Error: opts\n");
    }
    opts = (opts | O_NONBLOCK);
    if (fcntl(sockfd, F_SETFL, opts) < 0) {
        printf("Error fcntl\n");
    }
    if (bind(sockfd, (struct sockaddr *) &serv_addr,
        sizeof(serv_addr)) < 0) 
        error("ERROR on binding");
    listen(sockfd, MAX_CLIENTS); // max 20 in queue

    clilen = sizeof(cli_addr);

    // set up pool for incoming connections
    static Pool pool;
    init_pool(&pool, sockfd);

    /* TODO:
       ERROR HANDLING:
        - clientID can be 19 chars max (null terminator counts as one) - remove_client
        - client data is empty or wrong size - remove_client
        - len/id not an int - remove_client
        - Client arbitrarily closing the socket (this should be treated as a temporary disconnection,
            and its client record must not be removed)
        - Data part of a message is not equal to the bytes specified - remove_client
        - ClientID sent later (e.g. CHAT) does not match the original clientID that was set during HELLO - remove_client
        - If time, handle when partial messages come (e.g. test client sends only type section of header) - must wait until next read(s) give all necessary data to act upon it
    */
    while (1) {
        pool.read_set = pool.active_set; // save the current state
        // TODO: write_set messes it up and always returns true for some reason
         // pool.write_set = pool.active_set;
        pool.nready = select(pool.maxfd + 1, &pool.read_set, NULL, NULL, NULL);

        if (FD_ISSET(sockfd, &pool.read_set)) { // check if there is an incoming connection
            newsockfd = accept(sockfd, (struct sockaddr *) &cli_addr,
                &clilen);
            if (newsockfd < 0)
                error("ERROR on accept");
            add_client(sockfd, newsockfd, &pool); // add client by their socket id
            FD_CLR(sockfd, &pool.read_set);
        }
        check_clients(&pool);
    }
    close(sockfd);    
    return 0; 
}
