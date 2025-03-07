--
-- PostgreSQL database dump
--

-- Dumped from database version 16.1
-- Dumped by pg_dump version 16.1

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

ALTER TABLE ONLY public.messages DROP CONSTRAINT messages_chat_id_fkey;
ALTER TABLE ONLY public.messages DROP CONSTRAINT messages_author_id_fkey;
ALTER TABLE ONLY public.chats_users DROP CONSTRAINT chats_users_user_id_fkey;
ALTER TABLE ONLY public.chats_users DROP CONSTRAINT chats_users_last_read_message_fkey;
ALTER TABLE ONLY public.chats_users DROP CONSTRAINT chats_users_chat_id_fkey;
DROP TRIGGER update_last_active_trigger ON public.messages;
ALTER TABLE ONLY public.users DROP CONSTRAINT users_user_tag_key;
ALTER TABLE ONLY public.users DROP CONSTRAINT users_user_id_user_id1_key;
ALTER TABLE ONLY public.users DROP CONSTRAINT users_pkey;
ALTER TABLE ONLY public.users DROP CONSTRAINT users_firebase_id_key;
ALTER TABLE ONLY public.messages DROP CONSTRAINT messages_pkey;
ALTER TABLE ONLY public.chats DROP CONSTRAINT chats_pkey;
ALTER TABLE public.users ALTER COLUMN user_id DROP DEFAULT;
ALTER TABLE public.messages ALTER COLUMN message_id DROP DEFAULT;
ALTER TABLE public.chats ALTER COLUMN chat_id DROP DEFAULT;
DROP SEQUENCE public.users_user_id_seq;
DROP TABLE public.users;
DROP SEQUENCE public.messages_message_id_seq;
DROP TABLE public.messages;
DROP TABLE public.chats_users;
DROP SEQUENCE public.chats_chat_id_seq;
DROP TABLE public.chats;
DROP FUNCTION public.update_chat_last_active();
-- *not* dropping schema, since initdb creates it
--
-- Name: public; Type: SCHEMA; Schema: -; Owner: postgres
--

-- *not* creating schema, since initdb creates it


ALTER SCHEMA public OWNER TO postgres;

--
-- Name: SCHEMA public; Type: COMMENT; Schema: -; Owner: postgres
--

COMMENT ON SCHEMA public IS '';


--
-- Name: update_chat_last_active(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.update_chat_last_active() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
  UPDATE chats_users
  SET last_active = NEW.time_sent
  FROM messages
  WHERE messages.chat_id = NEW.chat_id;
  RETURN NEW;
END;
$$;


ALTER FUNCTION public.update_chat_last_active() OWNER TO postgres;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: chats; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.chats (
    chat_id integer NOT NULL,
    creation_time timestamp(0) without time zone NOT NULL,
    name text
);


ALTER TABLE public.chats OWNER TO postgres;

--
-- Name: chats_chat_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.chats_chat_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.chats_chat_id_seq OWNER TO postgres;

--
-- Name: chats_chat_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.chats_chat_id_seq OWNED BY public.chats.chat_id;


--
-- Name: chats_users; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.chats_users (
    chat_id integer NOT NULL,
    user_id integer NOT NULL,
    join_time timestamp(0) without time zone NOT NULL,
    last_read_message integer,
    last_active timestamp(0) without time zone
);


ALTER TABLE public.chats_users OWNER TO postgres;

--
-- Name: messages; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.messages (
    message_id integer NOT NULL,
    chat_id integer NOT NULL,
    author_id integer NOT NULL,
    time_sent timestamp(0) without time zone NOT NULL,
    content text NOT NULL
);


ALTER TABLE public.messages OWNER TO postgres;

--
-- Name: messages_message_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.messages_message_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.messages_message_id_seq OWNER TO postgres;

--
-- Name: messages_message_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.messages_message_id_seq OWNED BY public.messages.message_id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.users (
    user_id integer NOT NULL,
    firebase_id character varying(32) NOT NULL,
    user_tag character varying(16) NOT NULL,
    user_name character varying(64) NOT NULL
);


ALTER TABLE public.users OWNER TO postgres;

--
-- Name: users_user_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.users_user_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.users_user_id_seq OWNER TO postgres;

--
-- Name: users_user_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.users_user_id_seq OWNED BY public.users.user_id;


--
-- Name: chats chat_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.chats ALTER COLUMN chat_id SET DEFAULT nextval('public.chats_chat_id_seq'::regclass);


--
-- Name: messages message_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.messages ALTER COLUMN message_id SET DEFAULT nextval('public.messages_message_id_seq'::regclass);


--
-- Name: users user_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users ALTER COLUMN user_id SET DEFAULT nextval('public.users_user_id_seq'::regclass);


--
-- Name: chats chats_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.chats
    ADD CONSTRAINT chats_pkey PRIMARY KEY (chat_id);


--
-- Name: messages messages_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.messages
    ADD CONSTRAINT messages_pkey PRIMARY KEY (message_id);


--
-- Name: users users_firebase_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_firebase_id_key UNIQUE (firebase_id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (user_id);


--
-- Name: users users_user_id_user_id1_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_user_id_user_id1_key UNIQUE (user_id) INCLUDE (user_id);


--
-- Name: users users_user_tag_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_user_tag_key UNIQUE (user_tag);


--
-- Name: messages update_last_active_trigger; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER update_last_active_trigger AFTER INSERT ON public.messages FOR EACH ROW EXECUTE FUNCTION public.update_chat_last_active();


--
-- Name: chats_users chats_users_chat_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.chats_users
    ADD CONSTRAINT chats_users_chat_id_fkey FOREIGN KEY (chat_id) REFERENCES public.chats(chat_id) NOT VALID;


--
-- Name: chats_users chats_users_last_read_message_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.chats_users
    ADD CONSTRAINT chats_users_last_read_message_fkey FOREIGN KEY (last_read_message) REFERENCES public.messages(message_id) NOT VALID;


--
-- Name: chats_users chats_users_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.chats_users
    ADD CONSTRAINT chats_users_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(user_id) NOT VALID;


--
-- Name: messages messages_author_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.messages
    ADD CONSTRAINT messages_author_id_fkey FOREIGN KEY (author_id) REFERENCES public.users(user_id) NOT VALID;


--
-- Name: messages messages_chat_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.messages
    ADD CONSTRAINT messages_chat_id_fkey FOREIGN KEY (chat_id) REFERENCES public.chats(chat_id) NOT VALID;


--
-- Name: SCHEMA public; Type: ACL; Schema: -; Owner: postgres
--

REVOKE USAGE ON SCHEMA public FROM PUBLIC;


--
-- PostgreSQL database dump complete
--

