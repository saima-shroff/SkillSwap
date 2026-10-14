<script setup>
import { ArrowDownRight, ArrowRight, ArrowUpRight, BookOpen, Code2, HeartHandshake, Palette, Sparkles, UsersRound } from '@lucide/vue'
</script>

<template>
  <div class="page">
    <section class="hero">
      <div class="hero-copy">
        <div class="eyebrow">The internet's skill-sharing circle</div>
        <h1>Trade what you know.<br /><span>Learn what's next.</span></h1>
        <p>Meet curious people, exchange real-world skills, and grow in ways that feel good. No course fees, no gatekeeping — just people helping people.</p>
        <div class="hero-actions">
          <RouterLink class="button button-lime" to="/register">Find your next skill <ArrowUpRight :size="16" /></RouterLink>
          <RouterLink class="button button-outline" to="/explore">Explore skills <ArrowRight :size="15" /></RouterLink>
        </div>
        <div class="social-proof">
          <div class="avatar-stack"><span class="avatar">J</span><span class="avatar">M</span><span class="avatar">A</span><span class="avatar">+</span></div>
          <span><strong>Good things grow together.</strong> Join a generous community.</span>
        </div>
      </div>
      <div class="hero-visual">
        <div class="orbit">
          <div class="orbit-center"><HeartHandshake :size="54" /></div>
          <div class="float-card one"><span class="skill-tag"><Code2 :size="12" /> CAN TEACH</span><strong>Web development</strong><small>Alex · 1.2 mi away</small></div>
          <div class="float-card two"><span class="skill-tag badge-violet"><Palette :size="12" /> WANTS TO LEARN</span><strong>Brand illustration</strong><small>Trade skills, not money</small></div>
        </div>
      </div>
    </section>
    <section class="feature-strip">
      <div class="feature"><span class="feature-icon"><UsersRound :size="19" /></span><div><strong>People-first learning</strong><span>Learn together, at your own pace.</span></div></div>
      <div class="feature"><span class="feature-icon"><BookOpen :size="19" /></span><div><strong>Your skills have value</strong><span>Everyone has something to share.</span></div></div>
      <div class="feature"><span class="feature-icon"><Sparkles :size="19" /></span><div><strong>Good things compound</strong><span>One exchange can open new doors.</span></div></div>
    </section>
    <section class="section-heading">
      <div><div class="eyebrow">Make your next move</div><h2>Give a little. Get a lot.</h2></div>
      <RouterLink class="button button-outline button-small" to="/explore">Browse the community <ArrowDownRight :size="15" /></RouterLink>
    </section>
  </div>
</template>
