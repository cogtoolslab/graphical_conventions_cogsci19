library(Rfast)

########################

# whiten takes a matrix of features and z-scores within feature dimensions
whiten <- function(feats) {
  feat_centroid <- Rfast::colmeans(feats, parallel = T)
  feat_sd <- Rfast::colVars(feats, std = T, parallel = T)
  feat_sd <- ifelse(feat_sd == 0, 1e-5, feat_sd)
  return(t(apply(feats, 1, function(x) {(x - feat_centroid)/feat_sd})))
} 

# whitenF does some jiu jitsu to build a new F matrix with the whitened values
# note: the cbind(...) step is super slow (presumably because it has to concatenate
# all these data.frames with 4000 rows each?) 
# may be able to directly index F_out for each group instead of concatenating and then
# setting... 
whitenF <- function(M_mat, F_mat, how) {
  F_out <- matrix(data = NA, nrow = dim(F_mat)[1], ncol = dim(F_mat)[2])
  if(how == 'by_game') {
    grouped_M <- M_mat %>% group_by(gameID, target)
  } else if (how == 'by_target') {
    grouped_M <- M_mat %>% group_by(target)
  }
  F.df <- grouped_M %>%
    do(cbind(feature_ind = .$feature_ind, repetition = .$repetition, 
             as.data.frame(whiten(F_mat[.$feature_ind,])))) %>%
    ungroup() %>%
    arrange(feature_ind) 
  F_out[F.df$feature_ind,] <- data.matrix(F.df %>% select(starts_with('V')))
  return(F_out)
}

# note: cor expects featurs to be in columns so we transpose
get_sim_matrix = function(df, F_mat, method = 'cor') {
  feats <- F_mat[df$feature_ind,]
  if(method == 'cor') {
    return(cor(t(feats), method = 'pearson'))
  } else if (method == 'euclidean') {
    return(as.matrix(dist(feats, method = 'euclidean')))
  } else {
    stop(paste0('unknown method', method))
  }
}

average_sim_matrix <- function(cormat) {
  ut <- lower.tri(cormat)
  return(mean(cormat[ut]))
}

flatten_sim_matrix <- function(cormat) {
  ut <- upper.tri(cormat)
  data.frame(
    game1 = seq(0,nrow(ut))[row(cormat)[ut]],
    game2 = seq(0,ncol(ut))[col(cormat)[ut]],
    sim  = cormat[ut]
  )
}

compute_within_similarity <- function(M_mat, id, nboot = 1) {
  cat('\r', id, '/100')
  return(M_mat %>%
           complete(nesting(gameID, target), repetition) %>%  # Fill in NAs for missing repetitions
           group_by(gameID, target) %>%
           do(flatten_sim_matrix(get_sim_matrix(., F_by_game, method = 'euclidean'))) %>%
           filter(rep2 == rep1 + 1) %>%                       # only interested in successive reps
           group_by(rep1, rep2) %>%
           tidyboot_mean(col = cor, na.rm = T, nboot = nboot) %>%
           unite(`rep diff`, rep1, rep2, sep = '->')) %>%
    mutate(sample_id = id)
}

compute_across_similarity <- function(M_mat, id, nboot = 1) {
  cat('\r', id, '/100')
  M_mat %>%
    group_by(target, repetition) %>%
    do(summarize(., m = average_sim_matrix(get_sim_matrix(., F_by_target, method = 'euclidean')))) %>%
    group_by(repetition) %>%
    tidyboot_mean(col = m, nboot) %>%
    mutate(sample_id = id)
}
