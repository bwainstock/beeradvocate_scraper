�
,mzTc           @   s�   d  d l  Z  d  d l m Z d  d l Z d  d l Z d �  Z d �  Z d �  Z e d k r� e �  \ Z	 Z
 e e	 e
 � Z e e � Z e Ge e � GHn  d S(   i����N(   t   BeautifulSoupc       
   C   sl   t  j d d � }  |  j d d t d d d t d d	 �|  j d
 d t d d �|  j �  } | j | j f S(   sI   Parses command line arguments for city and two-letter state abbreviation.t   descriptions-   Returns Beer Advocate geodata for City, States   --cityt   typet   nargst   +t   requiredt   helpt   Citys   --states   Two letter state abreviation(   t   argparset   ArgumentParsert   add_argumentt   strt   Truet
   parse_argst   cityt   state(   t   parsert   args(    (    s
   ba_geo2.pyt   cliargs   s    c   
      C   s  g  } d } t  j | d | d j |  � f � } t | j � } | j | � | j d d i d d 6�} | d j } t j	 d | � } t
 | d � } g  t d	 d	 | d	 d
 d	 � D]" } | | | d j |  � f ^ q� } x9 | D]1 }	 t  j |	 � } t | j � } | j | � q� W| S(   sL   Determines number of reviews for a city and returns a list of response data.sR   http://www.beeradvocate.com/place/list/?start=%s&c_id=US&s_id=%s&city=%s&sort=namei    R   t   tdt   attrss   #000000t   bgcolors   (\d+)(?!.*\d)i   i   (   t   requestst   gett   joinR    t   contentt   appendt   findAllt   textt   ret   findallt   intt   range(
   R   R   t	   responsest   base_urlt   responset   datat   num_resultst   startt   url_listt   url(    (    s
   ba_geo2.pyt   get_beer   s     %Dc         C   sd   g  } xW |  D]O } g  | j  d d i d d 6d d 6�D] } | j �  ^ q7 } | j | � q W| S(   s>   Parses BeautifulSoup response and returns a list of the names.R   R   i   t   colspant   leftt   align(   R   t   getTextt   extend(   t   response_datat   barsR$   t   namet   names(    (    s
   ba_geo2.pyt   parse,   s    -t   __main__(   R   t   bs4R    R   R   R   R)   R3   t   __name__t   CITYt   STATEt   RESPONSEt	   BAR_NAMESt   len(    (    (    s
   ba_geo2.pyt   <module>   s   			