TABLESPACE pg_default;

-- Run this from psql command line
-- psql "postgresql://postgres:<secret>@34.172.34.239:5432/healthcare" -f healthcare_indexes.sql

-- # --------------------- INDEXES --------------------------------- #
 CREATE INDEX IF NOT EXISTS idx_product_version_id ON public.product_version USING btree (product_version_id);
 CREATE INDEX IF NOT EXISTS idx_product_id ON public.product_version USING btree (product_id);
 CREATE INDEX IF NOT EXISTS idx_product_version ON public.product_version USING btree (version);
 CREATE INDEX IF NOT EXISTS idx_patient_id ON public.claim USING btree (patient_id);
 CREATE INDEX IF NOT EXISTS idx_member_id ON public.member USING btree (member_id);
 CREATE INDEX IF NOT EXISTS idx_provider_id ON public.provider USING btree (provider_id);
 CREATE INDEX IF NOT EXISTS idx_attprovider_id ON public.claim USING btree (attendingprovider_id);
 CREATE INDEX IF NOT EXISTS idx_claim_id ON public.claim USING btree (claim_id) INCLUDE (claim_id);
 CREATE INDEX IF NOT EXISTS idx_claimline_claim_id ON public.claim_claimline USING btree (claim_id) INCLUDE (claim_id);
 CREATE INDEX IF NOT EXISTS ix_note_claim_id ON public.claim_notes USING btree (claim_id) INCLUDE (claim_id);
 CREATE INDEX IF NOT EXISTS idx_payment_claim_id ON public.claim_payment USING btree (claim_id) INCLUDE (claim_id);
 CREATE INDEX IF NOT EXISTS idx_diagnosis_claim_id ON public.claim_diagnosiscode USING btree (claim_id) INCLUDE (claim_id);
 CREATE INDEX IF NOT EXISTS idx_claimline_diagnosis_claimline_id ON public.claim_claimline_diagnosiscodes USING btree (claim_claimline_id) INCLUDE (claim_claimline_id);

-- # ------------------- CONSTRAINTS ------------------------------------ # 
ALTER TABLE ONLY public.claim
    ADD CONSTRAINT fkey_patient_id FOREIGN KEY (patient_id) REFERENCES public.member(member_id) NOT VALID;
-- Name: claim fkey_provider_id; Type: FK CONSTRAINT; Schema: public; Owner: bbadmin
ALTER TABLE ONLY public.claim
    ADD CONSTRAINT fkey_provider_id FOREIGN KEY (attendingprovider_id) REFERENCES public.provider(provider_id) NOT VALID;
-- Name: claim_claimline_diagnosiscodes fky_claim_claimline_id; Type: FK CONSTRAINT; Schema: public; Owner: bbadmin
ALTER TABLE ONLY public.claim_claimline_diagnosiscodes
    ADD CONSTRAINT fky_claim_claimline_id FOREIGN KEY (claim_claimline_id) REFERENCES public.claim_claimline(claim_claimline_id) NOT VALID;
-- Name: claim_claimline_payment fky_claim_claimline_id; Type: FK CONSTRAINT; Schema: public; Owner: bbadmin
ALTER TABLE ONLY public.claim_claimline_payment
    ADD CONSTRAINT fky_claim_claimline_id FOREIGN KEY (claim_claimline_id) REFERENCES public.claim_claimline(claim_claimline_id) NOT VALID;
-- Name: claim_diagnosiscode fky_claim_id; Type: FK CONSTRAINT; Schema: public; Owner: bbadmin
ALTER TABLE ONLY public.claim_diagnosiscode
    ADD CONSTRAINT fky_claim_id FOREIGN KEY (claim_id) REFERENCES public.claim(claim_id) NOT VALID;
-- Name: claim_notes fky_claim_id; Type: FK CONSTRAINT; Schema: public; Owner: bbadmin
ALTER TABLE ONLY public.claim_notes
    ADD CONSTRAINT fky_claim_id FOREIGN KEY (claim_id) REFERENCES public.claim(claim_id) NOT VALID;
-- Name: claim_payment fky_claim_id; Type: FK CONSTRAINT; Schema: public; Owner: bbadmin
ALTER TABLE ONLY public.claim_payment
    ADD CONSTRAINT fky_claim_id FOREIGN KEY (claim_id) REFERENCES public.claim(claim_id) NOT VALID;
-- Name: claim_claimline fky_claim_id; Type: FK CONSTRAINT; Schema: public; Owner: bbadmin
ALTER TABLE ONLY public.claim_claimline
    ADD CONSTRAINT fky_claim_id FOREIGN KEY (claim_id) REFERENCES public.claim(claim_id) NOT VALID;
-- Name: member_guardian_address fky_member_guardian_id; Type: FK CONSTRAINT; Schema: public; Owner: bbadmin
ALTER TABLE ONLY public.member_guardian_address
    ADD CONSTRAINT fky_member_guardian_id FOREIGN KEY (member_guardian_id) REFERENCES public.member_guardian(member_guardian_id) NOT VALID;
-- Name: member_address fky_member_id; Type: FK CONSTRAINT; Schema: public; Owner: bbadmin
ALTER TABLE ONLY public.member_address
    ADD CONSTRAINT fky_member_id FOREIGN KEY (member_id) REFERENCES public.member(member_id) NOT VALID;
-- Name: member_communication fky_member_id; Type: FK CONSTRAINT; Schema: public; Owner: bbadmin
ALTER TABLE ONLY public.member_communication
    ADD CONSTRAINT fky_member_id FOREIGN KEY (member_id) REFERENCES public.member(member_id) NOT VALID;
-- Name: member_languages fky_member_id; Type: FK CONSTRAINT; Schema: public; Owner: bbadmin
ALTER TABLE ONLY public.member_languages
    ADD CONSTRAINT fky_member_id FOREIGN KEY (member_id) REFERENCES public.member(member_id) NOT VALID;
-- Name: member_guardian fky_member_id; Type: FK CONSTRAINT; Schema: public; Owner: bbadmin
ALTER TABLE ONLY public.member_guardian
    ADD CONSTRAINT fky_member_id FOREIGN KEY (member_id) REFERENCES public.member(member_id) NOT VALID;
-- Name: member_bankaccount fky_member_id; Type: FK CONSTRAINT; Schema: public; Owner: bbadmin
ALTER TABLE ONLY public.member_bankaccount
    ADD CONSTRAINT fky_member_id FOREIGN KEY (member_id) REFERENCES public.member(member_id) NOT VALID;
-- Name: member_employment fky_member_id; Type: FK CONSTRAINT; Schema: public; Owner: bbadmin
ALTER TABLE ONLY public.member_employment
    ADD CONSTRAINT fky_member_id FOREIGN KEY (member_id) REFERENCES public.member(member_id) NOT VALID;
-- Name: member_disability fky_member_id; Type: FK CONSTRAINT; Schema: public; Owner: bbadmin
ALTER TABLE ONLY public.member_disability
    ADD CONSTRAINT fky_member_id FOREIGN KEY (member_id) REFERENCES public.member(member_id) NOT VALID;
-- Name: provider_languages fky_provider_id; Type: FK CONSTRAINT; Schema: public; Owner: bbadmin
ALTER TABLE ONLY public.provider_languages
    ADD CONSTRAINT fky_provider_id FOREIGN KEY (provider_id) REFERENCES public.provider(provider_id) NOT VALID;
-- Name: provider_dea fky_provider_id; Type: FK CONSTRAINT; Schema: public; Owner: bbadmin
ALTER TABLE ONLY public.provider_dea
    ADD CONSTRAINT fky_provider_id FOREIGN KEY (provider_id) REFERENCES public.provider(provider_id) NOT VALID;
-- Name: provider_hospitaladmittingprivileges fky_provider_id; Type: FK CONSTRAINT; Schema: public; Owner: bbadmin
ALTER TABLE ONLY public.provider_hospitaladmittingprivileges
    ADD CONSTRAINT fky_provider_id FOREIGN KEY (provider_id) REFERENCES public.provider(provider_id) NOT VALID;
-- Name: provider_specialties fky_provider_id; Type: FK CONSTRAINT; Schema: public; Owner: bbadmin
ALTER TABLE ONLY public.provider_specialties
    ADD CONSTRAINT fky_provider_id FOREIGN KEY (provider_id) REFERENCES public.provider(provider_id) NOT VALID;
-- Name: provider_license fky_provider_id; Type: FK CONSTRAINT; Schema: public; Owner: bbadmin
ALTER TABLE ONLY public.provider_license
    ADD CONSTRAINT fky_provider_id FOREIGN KEY (provider_id) REFERENCES public.provider(provider_id) NOT VALID;
-- Name: provider_medicaid fky_provider_id; Type: FK CONSTRAINT; Schema: public; Owner: bbadmin
ALTER TABLE ONLY public.provider_medicaid
    ADD CONSTRAINT fky_provider_id FOREIGN KEY (provider_id) REFERENCES public.provider(provider_id) NOT VALID;
-- Name: provider_medicare fky_provider_id; Type: FK CONSTRAINT; Schema: public; Owner: bbadmin
ALTER TABLE ONLY public.provider_medicare
    ADD CONSTRAINT fky_provider_id FOREIGN KEY (provider_id) REFERENCES public.provider(provider_id) NOT VALID;
