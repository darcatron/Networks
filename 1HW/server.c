/* Mathurshan Vimalesvaran */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <arpa/inet.h>
#include <sys/types.h> 
#include <sys/socket.h>
#include <netdb.h>
#include <netinet/in.h>

void error(const char *msg)
{
    perror(msg);
    exit(1);
}

typedef struct Visitor
{
    char *ip;
    char *hostname;
    char *user_agent;
} Visitor;


char *str_replace(char *orig, char *rep, char *with) {
    char *result; // the return string
    char *ins;    // the next insert point
    char *tmp;    // varies
    int len_rep;  // length of rep
    int len_with; // length of with
    int len_front; // distance between rep and end of last rep
    int count;    // number of replacements

    if (!orig)
        return NULL;
    if (!rep)
        rep = "";
    len_rep = strlen(rep);
    if (!with)
        with = "";
    len_with = strlen(with);

    ins = orig;
    for (count = 0; tmp = strstr(ins, rep); ++count) {
        ins = tmp + len_rep;
    }

    // first time through the loop, all the variable are set correctly
    // from here on,
    //    tmp points to the end of the result string
    //    ins points to the next occurrence of rep in orig
    //    orig points to the remainder of orig after "end of rep"
    tmp = result = malloc(strlen(orig) + (len_with - len_rep) * count + 1);

    if (!result)
        return NULL;

    while (count--) {
        ins = strstr(orig, rep);
        len_front = ins - orig;
        tmp = strncpy(tmp, orig, len_front) + len_front;
        tmp = strcpy(tmp, with) + len_with;
        orig += len_front + len_rep; // move to next "end of rep"
    }
    strcpy(tmp, orig);
    return result;
}

int main(int argc, char *argv[])
{
    int sockfd, newsockfd, portno;
    socklen_t clilen;
    int buffer_size = 512;
    char buffer[buffer_size];
    struct sockaddr_in serv_addr, cli_addr;
    int n;
    if (argc < 2) {
        fprintf(stderr,"ERROR, no port provided\n");
        exit(1);
    }
    
    sockfd = socket(AF_INET, SOCK_STREAM, 0);
    if (sockfd < 0) 
        error("ERROR opening socket");
    
    bzero((char *) &serv_addr, sizeof(serv_addr));
    portno = atoi(argv[1]);
    serv_addr.sin_family = AF_INET;
    serv_addr.sin_addr.s_addr = INADDR_ANY;
    serv_addr.sin_port = htons(portno);
    if (bind(sockfd, (struct sockaddr *) &serv_addr,
        sizeof(serv_addr)) < 0) 
        error("ERROR on binding");
    listen(sockfd,5);

    clilen = sizeof(cli_addr);
    struct addr_info *result;

    int MAX_VISITORS = 10;
    Visitor recent_visitors[MAX_VISITORS];
    int num_visitors = 0;
    int newest_visitor = -1; // where the list should start printing from
    int oldest_visitor = 0;
    
    while (1) {
        newsockfd = accept(sockfd, 
            (struct sockaddr *) &cli_addr,
            &clilen);
        if (newsockfd < 0)
            error("ERROR on accept");

        char *ip;
        ip = inet_ntoa(cli_addr.sin_addr);
        
        struct hostent *cli_info = gethostbyaddr(&cli_addr.sin_addr.s_addr, sizeof cli_addr.sin_addr.s_addr, AF_INET);

        bzero(buffer, buffer_size);
        n = read(newsockfd,buffer, buffer_size);
        if (n < 0) error("ERROR reading from socket");

        char user_agent[256];
        strcpy(user_agent, strtok(strstr(buffer, "User-Agent:"), "\n"));
        strcpy(user_agent, str_replace(user_agent, "<", "&lt;"));
        strcpy(user_agent, str_replace(user_agent, ">", "&gt;"));
        strcpy(user_agent, str_replace(user_agent, "\"", "&qout;"));
        const char delim[11] = "GET \n";
        char *route;
        route = strtok(buffer, delim);

        if (strcmp(route, "/") == 0) {     
            if (num_visitors < 10) num_visitors++;
            Visitor new_visitor;

            new_visitor.ip = ip;
            new_visitor.hostname = cli_info->h_name;
            new_visitor.user_agent = user_agent;
            newest_visitor = ++newest_visitor % MAX_VISITORS;
            recent_visitors[newest_visitor] = new_visitor;
            if (newest_visitor == oldest_visitor && num_visitors > 1) {
                oldest_visitor = ++oldest_visitor % MAX_VISITORS;
            }

            int i;
            int index = newest_visitor;
            char output[2048] = "HTTP/1.1 200 OK\nContent - type: text/html\n\n<html><body><a href='/about.html'>About Me</a></br>";
            for (i = 0; i < num_visitors; i++)
            {
                strcat(output, "Client IP Address: ");
                strcat(output, recent_visitors[index].ip);
                strcat(output, "</br>");
                strcat(output, "Client Host Name: ");
                strcat(output, recent_visitors[index].hostname);
                strcat(output, "</br>");
                strcat(output, recent_visitors[index].user_agent);
                strcat(output, "</br></br>");
                index--;
                if (index == -1) {
                    index = MAX_VISITORS - 1;
                }
            }
            strcat(output, "</body></html>\n");
            n = write(newsockfd, output, sizeof output); 
            if (n < 0) error("ERROR writing to socket");
        }
        else if (strcmp(route, "/about.html") == 0) {
            char about[1024] = "HTTP/1.1 200 OK\nContent - type: text/html\n\n<html><body><a href='/'>Home</a></br>My name is Mathurshan and I am a senior at Tufts. The most common thing I enjoy is food.</body></html>";
            n = write(newsockfd, about, sizeof about);
            if (n < 0) error("ERROR writing to socket");
        }
        else {
            n = write(newsockfd, "HTTP/1.1 404 Not Found\n\n FAILURE", 32); 
            if (n < 0) error("ERROR writing to socket");
        }

        close(newsockfd);
    }
    close(sockfd);    
    return 0; 
}
