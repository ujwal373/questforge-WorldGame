(:rule trade-weapon
  (and (has player rare_ore) (needs blacksmith ore))
  (do (give blacksmith player sword)
      (set (needs blacksmith ore) false)
      (inc (trust blacksmith player) 0.2)))

(:rule spawn-bandits
  (and (> (danger forest) 0.7) (not festival_active))
  (do (spawn bandits forest)
      (dec (mood villagers) 0.3)))
