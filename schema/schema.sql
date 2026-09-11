--
-- PostgreSQL database dump
--

\restrict jvKJmKH4SSIscRefcdo4Cb9aKcZcpjMFoaB4GUcEEPlhcAekYadKx3O9Egujkxt

-- Dumped from database version 18.4
-- Dumped by pg_dump version 18.4

-- Started on 2026-08-19 21:44:04

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- TOC entry 224 (class 1259 OID 24805)
-- Name: cartoes_credito; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.cartoes_credito (
    id integer NOT NULL,
    usuario_id integer NOT NULL,
    nome character varying(120) NOT NULL,
    limite numeric(15,2) NOT NULL,
    dia_fechamento smallint NOT NULL,
    dia_vencimento smallint NOT NULL,
    conta_pagamento_id integer,
    criado_em timestamp without time zone DEFAULT now() NOT NULL,
    CONSTRAINT cartoes_credito_dia_fechamento_check CHECK (((dia_fechamento >= 1) AND (dia_fechamento <= 31))),
    CONSTRAINT cartoes_credito_dia_vencimento_check CHECK (((dia_vencimento >= 1) AND (dia_vencimento <= 31))),
    CONSTRAINT cartoes_credito_limite_check CHECK ((limite >= (0)::numeric))
);


ALTER TABLE public.cartoes_credito OWNER TO postgres;

--
-- TOC entry 223 (class 1259 OID 24804)
-- Name: cartoes_credito_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.cartoes_credito_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.cartoes_credito_id_seq OWNER TO postgres;

--
-- TOC entry 5092 (class 0 OID 0)
-- Dependencies: 223
-- Name: cartoes_credito_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.cartoes_credito_id_seq OWNED BY public.cartoes_credito.id;


--
-- TOC entry 226 (class 1259 OID 24834)
-- Name: categorias; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.categorias (
    id integer NOT NULL,
    usuario_id integer NOT NULL,
    nome character varying(80) NOT NULL,
    tipo character varying(10) NOT NULL,
    cor character varying(7),
    CONSTRAINT categorias_tipo_check CHECK (((tipo)::text = ANY ((ARRAY['receita'::character varying, 'despesa'::character varying])::text[])))
);


ALTER TABLE public.categorias OWNER TO postgres;

--
-- TOC entry 225 (class 1259 OID 24833)
-- Name: categorias_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.categorias_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.categorias_id_seq OWNER TO postgres;

--
-- TOC entry 5093 (class 0 OID 0)
-- Dependencies: 225
-- Name: categorias_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.categorias_id_seq OWNED BY public.categorias.id;


--
-- TOC entry 222 (class 1259 OID 24785)
-- Name: contas; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.contas (
    id integer NOT NULL,
    usuario_id integer NOT NULL,
    nome character varying(120) NOT NULL,
    banco character varying(120),
    tipo character varying(20) NOT NULL,
    criado_em timestamp without time zone DEFAULT now() NOT NULL,
    CONSTRAINT contas_tipo_check CHECK (((tipo)::text = ANY ((ARRAY['corrente'::character varying, 'poupanca'::character varying, 'carteira'::character varying])::text[])))
);


ALTER TABLE public.contas OWNER TO postgres;

--
-- TOC entry 221 (class 1259 OID 24784)
-- Name: contas_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.contas_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.contas_id_seq OWNER TO postgres;

--
-- TOC entry 5094 (class 0 OID 0)
-- Dependencies: 221
-- Name: contas_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.contas_id_seq OWNED BY public.contas.id;


--
-- TOC entry 230 (class 1259 OID 24887)
-- Name: lancamentos; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.lancamentos (
    id integer NOT NULL,
    usuario_id integer NOT NULL,
    conta_id integer,
    cartao_id integer,
    categoria_id integer,
    descricao character varying(255) NOT NULL,
    valor numeric(15,2) NOT NULL,
    data_lancamento date NOT NULL,
    data_compensacao date,
    status character varying(10) DEFAULT 'pendente'::character varying NOT NULL,
    transferencia_id integer,
    criado_em timestamp without time zone DEFAULT now() NOT NULL,
    CONSTRAINT lancamentos_check CHECK ((((conta_id IS NOT NULL) AND (cartao_id IS NULL)) OR ((conta_id IS NULL) AND (cartao_id IS NOT NULL)))),
    CONSTRAINT lancamentos_status_check CHECK (((status)::text = ANY ((ARRAY['compensado'::character varying, 'pendente'::character varying])::text[]))),
    CONSTRAINT lancamentos_valor_check CHECK ((valor <> (0)::numeric))
);


ALTER TABLE public.lancamentos OWNER TO postgres;

--
-- TOC entry 229 (class 1259 OID 24886)
-- Name: lancamentos_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.lancamentos_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.lancamentos_id_seq OWNER TO postgres;

--
-- TOC entry 5095 (class 0 OID 0)
-- Dependencies: 229
-- Name: lancamentos_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.lancamentos_id_seq OWNED BY public.lancamentos.id;


--
-- TOC entry 228 (class 1259 OID 24854)
-- Name: transferencias; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.transferencias (
    id integer NOT NULL,
    usuario_id integer NOT NULL,
    conta_origem_id integer NOT NULL,
    conta_destino_id integer NOT NULL,
    valor numeric(15,2) NOT NULL,
    data date NOT NULL,
    descricao character varying(255),
    criado_em timestamp without time zone DEFAULT now() NOT NULL,
    CONSTRAINT transferencias_check CHECK ((conta_origem_id <> conta_destino_id)),
    CONSTRAINT transferencias_valor_check CHECK ((valor > (0)::numeric))
);


ALTER TABLE public.transferencias OWNER TO postgres;

--
-- TOC entry 227 (class 1259 OID 24853)
-- Name: transferencias_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.transferencias_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.transferencias_id_seq OWNER TO postgres;

--
-- TOC entry 5096 (class 0 OID 0)
-- Dependencies: 227
-- Name: transferencias_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.transferencias_id_seq OWNED BY public.transferencias.id;


--
-- TOC entry 220 (class 1259 OID 24768)
-- Name: usuarios; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.usuarios (
    id integer NOT NULL,
    nome character varying(120) NOT NULL,
    email character varying(160) NOT NULL,
    senha_hash character varying(255) NOT NULL,
    criado_em timestamp without time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.usuarios OWNER TO postgres;

--
-- TOC entry 219 (class 1259 OID 24767)
-- Name: usuarios_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.usuarios_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.usuarios_id_seq OWNER TO postgres;

--
-- TOC entry 5097 (class 0 OID 0)
-- Dependencies: 219
-- Name: usuarios_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.usuarios_id_seq OWNED BY public.usuarios.id;


--
-- TOC entry 4885 (class 2604 OID 24808)
-- Name: cartoes_credito id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.cartoes_credito ALTER COLUMN id SET DEFAULT nextval('public.cartoes_credito_id_seq'::regclass);


--
-- TOC entry 4887 (class 2604 OID 24837)
-- Name: categorias id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.categorias ALTER COLUMN id SET DEFAULT nextval('public.categorias_id_seq'::regclass);


--
-- TOC entry 4883 (class 2604 OID 24788)
-- Name: contas id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.contas ALTER COLUMN id SET DEFAULT nextval('public.contas_id_seq'::regclass);


--
-- TOC entry 4890 (class 2604 OID 24890)
-- Name: lancamentos id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.lancamentos ALTER COLUMN id SET DEFAULT nextval('public.lancamentos_id_seq'::regclass);


--
-- TOC entry 4888 (class 2604 OID 24857)
-- Name: transferencias id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.transferencias ALTER COLUMN id SET DEFAULT nextval('public.transferencias_id_seq'::regclass);


--
-- TOC entry 4881 (class 2604 OID 24771)
-- Name: usuarios id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.usuarios ALTER COLUMN id SET DEFAULT nextval('public.usuarios_id_seq'::regclass);


--
-- TOC entry 4911 (class 2606 OID 24821)
-- Name: cartoes_credito cartoes_credito_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.cartoes_credito
    ADD CONSTRAINT cartoes_credito_pkey PRIMARY KEY (id);


--
-- TOC entry 4914 (class 2606 OID 24844)
-- Name: categorias categorias_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.categorias
    ADD CONSTRAINT categorias_pkey PRIMARY KEY (id);


--
-- TOC entry 4916 (class 2606 OID 24846)
-- Name: categorias categorias_usuario_id_nome_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.categorias
    ADD CONSTRAINT categorias_usuario_id_nome_key UNIQUE (usuario_id, nome);


--
-- TOC entry 4908 (class 2606 OID 24797)
-- Name: contas contas_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.contas
    ADD CONSTRAINT contas_pkey PRIMARY KEY (id);


--
-- TOC entry 4927 (class 2606 OID 24904)
-- Name: lancamentos lancamentos_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.lancamentos
    ADD CONSTRAINT lancamentos_pkey PRIMARY KEY (id);


--
-- TOC entry 4920 (class 2606 OID 24869)
-- Name: transferencias transferencias_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.transferencias
    ADD CONSTRAINT transferencias_pkey PRIMARY KEY (id);


--
-- TOC entry 4904 (class 2606 OID 24783)
-- Name: usuarios usuarios_email_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.usuarios
    ADD CONSTRAINT usuarios_email_key UNIQUE (email);


--
-- TOC entry 4906 (class 2606 OID 24781)
-- Name: usuarios usuarios_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.usuarios
    ADD CONSTRAINT usuarios_pkey PRIMARY KEY (id);


--
-- TOC entry 4912 (class 1259 OID 24832)
-- Name: idx_cartoes_usuario_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_cartoes_usuario_id ON public.cartoes_credito USING btree (usuario_id);


--
-- TOC entry 4917 (class 1259 OID 24852)
-- Name: idx_categorias_usuario_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_categorias_usuario_id ON public.categorias USING btree (usuario_id);


--
-- TOC entry 4909 (class 1259 OID 24803)
-- Name: idx_contas_usuario_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_contas_usuario_id ON public.contas USING btree (usuario_id);


--
-- TOC entry 4921 (class 1259 OID 24932)
-- Name: idx_lancamentos_cartao_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_lancamentos_cartao_id ON public.lancamentos USING btree (cartao_id);


--
-- TOC entry 4922 (class 1259 OID 24931)
-- Name: idx_lancamentos_conta_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_lancamentos_conta_id ON public.lancamentos USING btree (conta_id);


--
-- TOC entry 4923 (class 1259 OID 24933)
-- Name: idx_lancamentos_data_lancamento; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_lancamentos_data_lancamento ON public.lancamentos USING btree (data_lancamento);


--
-- TOC entry 4924 (class 1259 OID 24934)
-- Name: idx_lancamentos_transferencia_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_lancamentos_transferencia_id ON public.lancamentos USING btree (transferencia_id);


--
-- TOC entry 4925 (class 1259 OID 24930)
-- Name: idx_lancamentos_usuario_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_lancamentos_usuario_id ON public.lancamentos USING btree (usuario_id);


--
-- TOC entry 4918 (class 1259 OID 24885)
-- Name: idx_transferencias_usuario_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_transferencias_usuario_id ON public.transferencias USING btree (usuario_id);


--
-- TOC entry 4929 (class 2606 OID 24827)
-- Name: cartoes_credito cartoes_credito_conta_pagamento_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.cartoes_credito
    ADD CONSTRAINT cartoes_credito_conta_pagamento_id_fkey FOREIGN KEY (conta_pagamento_id) REFERENCES public.contas(id) ON DELETE SET NULL;


--
-- TOC entry 4930 (class 2606 OID 24822)
-- Name: cartoes_credito cartoes_credito_usuario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.cartoes_credito
    ADD CONSTRAINT cartoes_credito_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuarios(id) ON DELETE CASCADE;


--
-- TOC entry 4931 (class 2606 OID 24847)
-- Name: categorias categorias_usuario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.categorias
    ADD CONSTRAINT categorias_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuarios(id) ON DELETE CASCADE;


--
-- TOC entry 4928 (class 2606 OID 24798)
-- Name: contas contas_usuario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.contas
    ADD CONSTRAINT contas_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuarios(id) ON DELETE CASCADE;


--
-- TOC entry 4935 (class 2606 OID 24915)
-- Name: lancamentos lancamentos_cartao_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.lancamentos
    ADD CONSTRAINT lancamentos_cartao_id_fkey FOREIGN KEY (cartao_id) REFERENCES public.cartoes_credito(id);


--
-- TOC entry 4936 (class 2606 OID 24920)
-- Name: lancamentos lancamentos_categoria_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.lancamentos
    ADD CONSTRAINT lancamentos_categoria_id_fkey FOREIGN KEY (categoria_id) REFERENCES public.categorias(id);


--
-- TOC entry 4937 (class 2606 OID 24910)
-- Name: lancamentos lancamentos_conta_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.lancamentos
    ADD CONSTRAINT lancamentos_conta_id_fkey FOREIGN KEY (conta_id) REFERENCES public.contas(id);


--
-- TOC entry 4938 (class 2606 OID 24925)
-- Name: lancamentos lancamentos_transferencia_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.lancamentos
    ADD CONSTRAINT lancamentos_transferencia_id_fkey FOREIGN KEY (transferencia_id) REFERENCES public.transferencias(id);


--
-- TOC entry 4939 (class 2606 OID 24905)
-- Name: lancamentos lancamentos_usuario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.lancamentos
    ADD CONSTRAINT lancamentos_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuarios(id) ON DELETE CASCADE;


--
-- TOC entry 4932 (class 2606 OID 24880)
-- Name: transferencias transferencias_conta_destino_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.transferencias
    ADD CONSTRAINT transferencias_conta_destino_id_fkey FOREIGN KEY (conta_destino_id) REFERENCES public.contas(id);


--
-- TOC entry 4933 (class 2606 OID 24875)
-- Name: transferencias transferencias_conta_origem_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.transferencias
    ADD CONSTRAINT transferencias_conta_origem_id_fkey FOREIGN KEY (conta_origem_id) REFERENCES public.contas(id);


--
-- TOC entry 4934 (class 2606 OID 24870)
-- Name: transferencias transferencias_usuario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.transferencias
    ADD CONSTRAINT transferencias_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuarios(id) ON DELETE CASCADE;


-- Completed on 2026-08-19 21:44:05

--
-- PostgreSQL database dump complete
--

\unrestrict jvKJmKH4SSIscRefcdo4Cb9aKcZcpjMFoaB4GUcEEPlhcAekYadKx3O9Egujkxt

